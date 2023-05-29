from dataclasses import asdict
from functools import partial
import json
import os
import sys

from serial import Serial, SerialException
import asyncio
from websockets.server import serve, WebSocketServerProtocol

from src.relay import ReceiveState, Relay
from src.data import Vector, Data, DropData
from src.directory import Directory

commands = {
    'Accelerometer': 0,
    'Gyroscope': 1,
    'Waterproof': 2,
    'Ultrasonic': 3,
    'Air Quality': 4,
    'Sound': 5,
    'DHT inside': 6,
    'DHT outside': 7,
    'Run': 8,
    'Radio Channel': 9
}

enabled_sensors = {
    'Accelerometer': True,
    'Gyroscope': True,
    'Waterproof': True,
    'Ultrasonic': True,
    'Air Quality': True,
    'Sound': True,
    'DHT inside': True,
    'DHT outside': True
}

websocketDelay = 500

accelerationOffset = Vector(
    x=0.0890,
    y=0.4801,
    z=9.7219
)
gyroscopeOffset = Vector(
    x=-1.4647,
    y=-0.8470,
    z=-1.2042
)
insideTemepratureCoefficients = { 'k': 0.9153, 'm': 2.2295 }
insideHumidityCoefficients = { 'k': 1.0660, 'm': -2.5015 }
outsideHumidityCoefficients = { 'k': 0.9231, 'm': 3.3838 }

timestamps = []


def startTimeFromZero(data: Data):
    data.time -= timestamps[0]


def ignore_disabled_sensors(data: Data):
    if not enabled_sensors['Accelerometer']:
        data.acceleration = None
    if not enabled_sensors['Gyroscope']:
        data.gyroscope = None
    if not enabled_sensors['Waterproof']:
        data.temperature_outside = None
    if not enabled_sensors['Ultrasonic']:
        data.distance = None
    if not enabled_sensors['Air Quality']:
        data.air_quality = None
    if not enabled_sensors['Sound']:
        data.sound = None
    if not enabled_sensors['DHT inside']:
        data.temperature_inside = None
        data.humidity_inside = None
    if not enabled_sensors['DHT outside']:
        data.humidity_outside = None
    


def removeAccelerometerOffset(data: Data):
    if data.acceleration is not None:
        data.acceleration -= accelerationOffset


def removeGyroscopeOffset(data: Data):
    if data.gyroscope is not None:
        data.gyroscope -= gyroscopeOffset


def convertInsideTemperature(data: Data):
    if data.temperature_inside is not None:
        k = insideTemepratureCoefficients['k']
        m = insideTemepratureCoefficients['m']
        data.temperature_inside = k * data.temperature_inside + m


def convertInsideHumidity(data: Data):
    if data.humidity_inside is not None:
        k = insideHumidityCoefficients['k']
        m = insideHumidityCoefficients['m']
        data.humidity_inside = k * data.humidity_inside + m


def convertOutsideHumidity(data: Data):
    if data.humidity_outside is not None:
        k = outsideHumidityCoefficients['k']
        m = outsideHumidityCoefficients['m']
        data.humidity_outside = k * data.humidity_outside + m


def process_data(data: Data):
    removeAccelerometerOffset(data)
    removeGyroscopeOffset(data)

    convertInsideTemperature(data)
    convertInsideHumidity(data)
    convertOutsideHumidity(data)


def process_drop_data(data: DropData):
    removeAccelerometerOffset(data)
    removeGyroscopeOffset(data)


def removeNoneFromDictionary(dictionary: dict):
    return {
        key: value for key, value in dictionary.items()
        if value is not None
    }


def toggle_sensor(sensor: str, state: bool):
    global enabled_sensors

    enabled_sensors[sensor] = state


def sendCommand(serial: Serial, action: int, value: int):
    serial.write('01'.encode())
    serial.write(bytes([action, value]))


async def websocket_loop(websocket: WebSocketServerProtocol, serial: Serial):
    async for message in websocket:
        if ':' in message:
            action, value = message.split(':')
            if action in enabled_sensors:
                toggle_sensor(action, bool(value))
            sendCommand(serial, commands[action], int(value))
        else:
            print(message)


async def serial_loop(websocket: WebSocketServerProtocol, serial: Serial, relay: Relay, directory: Directory):
    global timestamps

    lastSentData: Data = None

    while websocket.open:
        match relay.receive_state:
            case ReceiveState.HEADER:
                relay.try_receive_header()
            case ReceiveState.TYPE:
                relay.try_receive_type()
            case ReceiveState.DATA:
                data = relay.try_receive_data()
                if data and not data.time in timestamps:
                    timestamps.append(data.time)
                    startTimeFromZero(data)

                    if data.time >= 0:
                        ignore_disabled_sensors(data)
                        process_data(data)

                        directory.saveData(data)
                        
                        filtered_data = removeNoneFromDictionary(asdict(data))

                        if (not lastSentData
                            or data.temperature_inside
                            or data.temperature_outside
                            or data.humidity_inside
                            or data.humidity_outside
                            or data.time - lastSentData.time >= websocketDelay):
                            await websocket.send(json.dumps(filtered_data))    
                            lastSentData = data
            case ReceiveState.DROP:
                data = relay.try_receive_drop_data()
                if data:
                    startTimeFromZero(data)

                    if data.time >= 0 and not data.time in timestamps:
                        timestamps.append(data.time)

                        process_drop_data(data)

                        directory.saveDropData(data)
                        
                        filtered_data = removeNoneFromDictionary(asdict(data))

                        if not lastSentData or data.time - lastSentData.time >= websocketDelay:
                            await websocket.send(json.dumps(filtered_data))    
                            lastSentData = data
                    
            case ReceiveState.TEXT:
                text = relay.try_receive_text()
                if text:
                    print(text)
        await asyncio.sleep(0)


async def on_websocket_connect(websocket: WebSocketServerProtocol, serial: Serial):
    global timestamps

    timestamps = []

    directory = Directory()
    relay = Relay(serial)

    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(serial_loop(websocket, serial, relay, directory))

        await websocket_loop(websocket, serial)


async def main():
    baud_rate = 115200
    com_port: int = None

    try:
        com_port = sys.argv[1]
    except IndexError:
        print(f'Usage: {sys.argv[0]} [COM Port]', file=sys.stderr)
        return

    try:
        with Serial(port=com_port, baudrate=baud_rate, timeout=0) as serial:
            async with serve(partial(on_websocket_connect, serial=serial), 'localhost', 8765):
                await asyncio.Future()
    except SerialException:
        print("Invalid COM Port")
        return


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Bye')
    os._exit(0)
