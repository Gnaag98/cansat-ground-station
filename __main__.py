from dataclasses import dataclass, asdict
from enum import Enum, IntEnum, auto
import json
import os
from struct import unpack
import sys
from datetime import datetime
import time

from serial import Serial, SerialException
import asyncio
from websockets.server import serve, WebSocketServerProtocol


@dataclass
class Acceleration:
    x: float
    y: float
    z: float


@dataclass
class Data:
    acceleration: Acceleration
    time: int
    WP_temp: float
    sound: int
    distance: int
    air_quality: int
    DHT11_temp_inside: int
    DHT11_hum_inside: int
    DHT11_temp_outside: int
    DHT11_hum_outside: int


class SerialState(Enum):
    IDLE = auto()
    RECEIVING_TYPE = auto()
    RECEIVING_DATA = auto()
    RECEIVING_TEXT = auto()


class SerialMessageType(IntEnum):
    DATA = ord('0')
    TEXT = ord('1')


samples = []
    
serial_data_wait_seconds = 1e-1
serial_text_wait_seconds = 1
serial_header_bytes = b'01'
serial_header_index = 0
serial_start_time: float
serial_state = SerialState.IDLE
serial_incoming_text = ''

def deserialize(serialized: bytes):
    deserialized = unpack('<fffLfhhhBBBB', serialized)

    acceleration = Acceleration(*deserialized[:3])
    remaining_variables = deserialized[3:]

    return Data(acceleration, *remaining_variables)


def respond(serial: Serial):
    serial.write('Thank you for the data\n'.encode())


def try_receive_text(serial: Serial) -> str | None:
    global serial_state
    global serial_incoming_text

    if serial_timeout(serial_text_wait_seconds):
        return None

    if serial.in_waiting > 0:
        byte = serial.read()[0]
        character = chr(byte)
        if character == '\n':
            serial_state = SerialState.IDLE
            return serial_incoming_text
        else:
            serial_incoming_text += character
    return None
        

def try_receive_data(serial: Serial) -> Data | None:
    global serial_header_index
    global serial_state

    if serial_timeout(serial_data_wait_seconds):
        return None

    if serial.in_waiting >= 30:
        serialized = serial.read(30)
        data = deserialize(serialized)
        serial_state = SerialState.IDLE
        return data
    else:
        return None


def process_data(data: Data, filename: str, serial: Serial):
    print(data)
    respond(serial)

    samples.append(asdict(data))

    with open(filename, 'w') as file:
        json.dump(samples, file, indent=4)


def try_receive_header(serial: Serial):
    global serial_header_index
    global serial_start_time
    global serial_state
    global serial_incoming_text

    if serial.in_waiting == 0:
        return
    
    byte = serial.read()[0]

    if serial_state == SerialState.RECEIVING_TYPE:
        match byte:
            case SerialMessageType.DATA:
                serial_state = SerialState.RECEIVING_DATA
                serial_start_time = time.perf_counter()
            case SerialMessageType.TEXT:
                serial_state = SerialState.RECEIVING_TEXT
                serial_start_time = time.perf_counter()
                serial_incoming_text = ''
            case _:
                serial_state = SerialState.IDLE
                print('Incorrect message type')
    elif byte == serial_header_bytes[serial_header_index]:
        serial_header_index += 1
        if serial_header_index == len(serial_header_bytes):
            serial_state = SerialState.RECEIVING_TYPE
            serial_header_index = 0
    else:
        serial_header_index = 0
        print(f"Incorrect start byte: '{chr(byte)}' = {byte}.")


def serial_timeout(max_duration: str):
    global serial_start_time
    global serial_state

    if time.perf_counter() - serial_start_time > max_duration:
        serial_state = SerialState.IDLE
        print('Timeout reached')
        return True
    else:
        return False


async def try_receive_websocket(websocket: WebSocketServerProtocol):
    try:
        async with asyncio.timeout(0):
            message = await websocket.recv()
            print(message)
    except TimeoutError:
        pass


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
            async def websocket_handler(websocket: WebSocketServerProtocol):
                # Code here will run when a websocket client connects.
                filename = datetime.today().strftime("data/data_%Y-%m-%d_%H.%M.%S.txt")

                while True:
                    await try_receive_websocket(websocket)

                    if serial_state == SerialState.RECEIVING_DATA:
                        data = try_receive_data(serial)
                        if data:
                            process_data(data, filename, serial)
                    elif serial_state == SerialState.RECEIVING_TEXT:
                        text = try_receive_text(serial)
                        if text:
                            print(text)
                    else:
                        try_receive_header(serial)

            async with serve(websocket_handler, 'localhost', 8765):
                await asyncio.Future()
    except SerialException:
        print("Invalid COM Port")
        return


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Bye')
    os._exit(0)
