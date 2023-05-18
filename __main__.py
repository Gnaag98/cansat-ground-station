from dataclasses import dataclass, asdict
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


samples = []


def deserialize(serialized: bytes):
    deserialized = unpack('<fffLfhhhBBBB', serialized)

    acceleration = Acceleration(*deserialized[:3])
    remaining_variables = deserialized[3:]

    return Data(acceleration, *remaining_variables)


def respond(serial: Serial):
    serial.write('Thank you for the data\n'.encode())


def receive(serial: Serial) -> Data | None:
    if serial.in_waiting >= 30:
        serialized = serial.read(30)
        data = deserialize(serialized)
        return data
    else:
        return None


def process_data(data: Data, filename: str, serial: Serial):
    print(data)
    respond(serial)

    samples.append(asdict(data))

    with open(filename, 'w') as file:
        json.dump(samples, file, indent=4)


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

                max_wait_seconds = 1e-3
                start_time: float
                is_receiving_serial = False

                while True:
                    if is_receiving_serial:
                        if time.perf_counter() - start_time > max_wait_seconds:
                            print('Timeout reached')
                            is_receiving_serial = False
                            continue

                        data = receive(serial)
                        if data:
                            process_data(data, filename, serial)
                            is_receiving_serial = False
                    else:
                        if serial.in_waiting > 0:
                            byte = serial.read()[0]
                            if (chr(byte) == '0'):
                                print('Message incoming: ', end='')
                                start_time = time.perf_counter()
                                is_receiving_serial = True
                            else:
                                print(chr(byte), end='', flush=True)
                        
                        await try_receive_websocket(websocket)
                

                    

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
