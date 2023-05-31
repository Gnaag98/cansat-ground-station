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

accelerationCoefficients = {
    'x': { 'k': 0.9852, 'm': -0.0049 },
    'y': { 'k': 1.0000, 'm': 0.0300 },
    'z': { 'k': 1.0363, 'm': -0.0466 }
}
gyroscopeOffset = Vector(
    x=-1.4647,
    y=-0.8470,
    z=-1.2042
)
insideTemepratureCoefficients = { 'k': 0.9921, 'm': -0.5465 }
insideHumidityCoefficients = { 'k': 0.9072, 'm': -0.2948 }
outsideHumidityCoefficients = { 'k': 0.9458, 'm': 2.3840 }

received_timestamps = []
first_received_timestamp: float = None
latest_received_timestamp: float = None

latest_sent_timestamp: float = None


def detect_strange_acceleration(acceleration: Vector) -> bool:
    max_value = 2 * 9.82
    if acceleration is None:
        return False
    else:
        return (
            abs(acceleration.x) > max_value
            or abs(acceleration.y) > max_value
            or abs(acceleration.z) > max_value
        )


def detect_strange_gyroscope(gyroscope: Vector) -> bool:
    max_value = 250
    if gyroscope is None:
        return False
    else:
        return (
            abs(gyroscope.x) > max_value
            or abs(gyroscope.y) > max_value
            or abs(gyroscope.z) > max_value
        )


def detect_strange_distance(distance: int | float) -> bool:
    max_value = 300
    if distance is None:
        return False
    else:
        return (
            distance < 0
            or distance > max_value
        )


def detect_strange_analog(analog_data: int | float) -> bool:
    max_value = 1023
    if analog_data is None:
        return False
    else:
        return (
            analog_data < 0
            or analog_data > max_value
        )


def detect_strange_temperature(temperature: int | float) -> bool:
    max_value = 100
    if temperature is None:
        return False
    else:
        return (
            temperature < 0
            or temperature > max_value
        )


def detect_strange_humidity(humidity: int | float) -> bool:
    max_value = 100
    if humidity is None:
        return False
    else:
        return (
            humidity < 0
            or humidity > max_value
        )


def detect_strange_data(data: Data) -> bool:
    return (
        detect_strange_acceleration(data.acceleration)
        or detect_strange_gyroscope(data.gyroscope)
        or detect_strange_distance(data.distance)
        or detect_strange_analog(data.air_quality)
        or detect_strange_analog(data.sound)
        or detect_strange_temperature(data.temperature_outside)
        or detect_strange_temperature(data.temperature_inside)
        or detect_strange_humidity(data.humidity_outside)
        or detect_strange_humidity(data.humidity_inside)
    )


def update_received_time(timestamp: float):
    global received_timestamps
    global first_received_timestamp
    global latest_received_timestamp

    received_timestamps.append(timestamp)

    if first_received_timestamp is None:
        first_received_timestamp = timestamp

    if latest_received_timestamp is None:
        latest_received_timestamp = timestamp
    else:
        latest_received_timestamp = max(timestamp, latest_received_timestamp)


def update_send_time(timestamp: float):
    global latest_sent_timestamp

    if latest_sent_timestamp is None:
        latest_sent_timestamp = timestamp
    else:
        latest_sent_timestamp = max(timestamp, latest_sent_timestamp)


def startTimeFromZero(data: Data | DropData):
    data.time -= received_timestamps[0]


def ignore_disabled_sensors_in_data(data: Data):
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


def ignore_disabled_sensors_in_drop_data(data: DropData):
    if not enabled_sensors['Accelerometer']:
        data.acceleration = None
    if not enabled_sensors['Gyroscope']:
        data.gyroscope = None


def convertAccelerometer(data: Data):
    if data.acceleration is not None:
        kX = accelerationCoefficients['x']['k']
        kY = accelerationCoefficients['y']['k']
        kZ = accelerationCoefficients['z']['k']

        mX = accelerationCoefficients['x']['m']
        mY = accelerationCoefficients['y']['m']
        mZ = accelerationCoefficients['z']['m']

        data.acceleration.x = kX * data.acceleration.x + mX
        data.acceleration.y = kY * data.acceleration.y + mY
        data.acceleration.z = kZ * data.acceleration.z + mZ

        data.acceleration.x *= 9.82
        data.acceleration.y *= 9.82
        data.acceleration.z *= 9.82


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
    convertAccelerometer(data)
    removeGyroscopeOffset(data)

    convertInsideTemperature(data)
    convertInsideHumidity(data)
    convertOutsideHumidity(data)


def process_drop_data(data: DropData):
    convertAccelerometer(data)
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
            value = int(value)
            if action in enabled_sensors:
                toggle_sensor(action, bool(value))
            sendCommand(serial, commands[action], value)
        else:
            print(message)


async def serial_loop(websocket: WebSocketServerProtocol, serial: Serial, relay: Relay, directory: Directory):
    global received_timestamps

    while websocket.open:
        await asyncio.sleep(0)

        match relay.receive_state:
            case ReceiveState.HEADER:
                relay.try_receive_header()

            case ReceiveState.TYPE:
                relay.try_receive_type()

            case ReceiveState.DATA:
                data = relay.try_receive_data()

                if not data:
                    # Abort if there is no data.
                    continue

                received_time = data.time

                if received_time < 0:
                    # Abort if the timestamp is negative.
                    print('[ERROR] Received timestamp is negative.')
                    continue
                if received_time in received_timestamps:
                    # Abort if the data has already been received.
                    print('[ERROR] Data with the same timestamp has already been received.')
                    continue

                if latest_received_timestamp:
                    time_since_first_receive = received_time - first_received_timestamp
                    if time_since_first_receive < 0:
                        # Abort if the data is older than the oldest.
                        # This might mess up the first few values if they are
                        # sent out of order, but that is an okay drawback.
                        print('[ERROR] Received data is older than the oldest data.')
                        continue

                    time_since_latest_receive = received_time - latest_received_timestamp
                    if time_since_latest_receive > 1000 * 60 * 10:
                        # Abort the data is more than 10 minutes older than the
                        # newest data.
                        print('[ERROR] Received data is more than 10 minutes older than the newest data.')
                        continue

                update_received_time(received_time)

                startTimeFromZero(data)
                ignore_disabled_sensors_in_data(data)
                process_data(data)

                directory.saveData(data)

                if (
                        # Send if this is the first time sending.
                        (not latest_sent_timestamp)
                        # Send if the data contains temperature or humidity data.
                        or (data.temperature_inside
                        or data.temperature_outside
                        or data.humidity_inside
                        or data.humidity_outside)
                        # Send if enough time has passed since the last data was sent.
                        or (received_time - latest_sent_timestamp >= websocketDelay)
                    ):
                    if detect_strange_data(data):
                        print('[WARNING] Strange date detected.')
                    else:
                        filtered_data = removeNoneFromDictionary(asdict(data))
                        await websocket.send(json.dumps(filtered_data))
                        update_send_time(received_time)

            case ReceiveState.DROP:
                data = relay.try_receive_drop_data()

                if not data:
                    # Abort if there is no data.
                    continue

                received_time = data.time

                if received_time < 0:
                    # Abort if the timestamp is negative.
                    print('[ERROR] Received timestamp is negative.')
                    continue
                if received_time in received_timestamps:
                    # Abort if the data has already been received.
                    print('[ERROR] Data with the same timestamp has already been received.')
                    continue

                if latest_received_timestamp:
                    time_since_first_receive = received_time - first_received_timestamp
                    if time_since_first_receive < 0:
                        # Abort if the data is older than the oldest.
                        # This might mess up the first few values if they are
                        # sent out of order, but that is an okay drawback.
                        print('[ERROR] Received data is older than the oldest data.')
                        continue

                    time_since_latest_receive = received_time - latest_received_timestamp
                    if time_since_latest_receive > 1000 * 60 * 10:
                        # Abort the data is more than 10 minutes older than the
                        # newest data.
                        print('[ERROR] Received data is more than 10 minutes older than the newest data.')
                        continue

                update_received_time(received_time)

                startTimeFromZero(data)
                ignore_disabled_sensors_in_drop_data(data)
                process_drop_data(data)

                directory.saveDropData(data)

                if (
                        # Send if this is the first time sending.
                        (not latest_sent_timestamp)
                        # Send if enough time has passed since the last data was sent.
                        or (received_time - latest_sent_timestamp >= websocketDelay)
                    ):
                    filtered_data = removeNoneFromDictionary(asdict(data))
                    await websocket.send(json.dumps(filtered_data))
                    update_send_time(received_time)
                    
            case ReceiveState.TEXT:
                text = relay.try_receive_text()
                if text:
                    print(text)


async def on_websocket_connect(websocket: WebSocketServerProtocol, serial: Serial):
    global received_timestamps

    received_timestamps = []

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
