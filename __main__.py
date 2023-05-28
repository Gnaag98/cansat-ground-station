from dataclasses import asdict
from functools import partial
import json
import os
import sys

from serial import Serial, SerialException
import asyncio
from websockets.server import serve, WebSocketServerProtocol

from src.relay import ReceiveState, Relay
from src.data import Vector, Data
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

samples = []
websocketDelay = 500

firstTimestamp: int
accelerationOffset = Vector(
    x= 9.9662,
    y=-0.2673,
    z= 0.0627
)
gyroscopeOffset = Vector(
    x=-0.3818,
    y=-0.2347,
    z=-0.2842
)
insideTemepratureCoefficients = { 'k': 0.9153, 'm': 2.2295 }
insideHumidityCoefficients = { 'k': 1.0660, 'm': -2.5015 }
outsideHumidityCoefficients = { 'k': 0.9231, 'm': 3.3838 }


def startTimeFromZero(data: Data):
    global firstTimestamp

    if not firstTimestamp:
        firstTimestamp = data.time

    data.time -= firstTimestamp


def removeAccelerometerOffset(data: Data):
    data.acceleration -= accelerationOffset


def removeGyroscopeOffset(data: Data):
    data.gyroscope -= gyroscopeOffset


def convertInsideTemperature(data: Data):
    k = insideTemepratureCoefficients['k']
    m = insideTemepratureCoefficients['m']
    data.temperature_inside = k * data.temperature_inside + m


def convertInsideHumidity(data: Data):
    k = insideHumidityCoefficients['k']
    m = insideHumidityCoefficients['m']
    data.humidity_inside = k * data.humidity_inside + m


def convertOutsideHumidity(data: Data):
    k = outsideHumidityCoefficients['k']
    m = outsideHumidityCoefficients['m']
    data.humidity_outside = k * data.humidity_outside + m


def sendCommand(serial: Serial, action: int, value: int):
    serial.write('01'.encode())
    serial.write(bytes([action, value]))


def process_data(data: Data, directory: Directory):
    startTimeFromZero(data)

    removeAccelerometerOffset(data)
    removeGyroscopeOffset(data)

    convertInsideTemperature(data)
    convertInsideHumidity(data)
    convertOutsideHumidity(data)

    samples.append(asdict(data))

    directory.save(data)


def removeNoneFromDictionary(dictionary: dict):
    return {
        key: value for key, value in dictionary.items()
        if value is not None
    }


async def websocket_loop(websocket: WebSocketServerProtocol, serial: Serial):
    async for message in websocket:
        if ':' in message:
            action, value = message.split(':')
            sendCommand(serial, commands[action], int(value))
        else:
            print(message)


async def serial_loop(websocket: WebSocketServerProtocol, serial: Serial, relay: Relay, directory: Directory):
    lastSentData: Data = None

    while websocket.open:
        match relay.receive_state:
            case ReceiveState.HEADER:
                relay.try_receive_header()
            case ReceiveState.TYPE:
                relay.try_receive_type()
            case ReceiveState.DATA:
                data = relay.try_receive_data()
                if data:
                    process_data(data, directory)

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
    global firstTimestamp

    firstTimestamp = None

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
