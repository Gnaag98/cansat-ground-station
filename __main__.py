from dataclasses import dataclass, asdict
import json
import os
from struct import unpack
import sys
from datetime import datetime
import time

import serial as pyserial
import asyncio


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


def deserialize(serialized: bytes):
    deserialized = unpack('<fffLfhhhBBBB', serialized)

    acceleration = Acceleration(*deserialized[:3])
    remaining_variables = deserialized[3:]

    return Data(acceleration, *remaining_variables)


def respond(serial: pyserial.Serial):
    serial.write('Thank you for the data\n'.encode())


def receive(serial: pyserial.Serial) -> Data:
    max_wait_seconds = 1e-3
    start_time: float

    while True:
        byte = 0

        while chr(byte) != '0':
            if serial.in_waiting > 0:
                byte = serial.read()[0]
                if chr(byte) == '0':
                    print('Message incoming: ', end='')
                    start_time = time.perf_counter()
                else:
                    print(chr(byte), end='')

        while time.perf_counter() - start_time < max_wait_seconds:
            if serial.in_waiting >= 30:
                serialized = serial.read(30)
                data = deserialize(serialized)
                return data


def serial_work(com_port: str, baud_rate: int):
    try:
        with pyserial.Serial(port=com_port, baudrate=baud_rate, timeout=0) as serial:
            filename = datetime.today().strftime("data/data_%Y-%m-%d_%H.%M.%S.txt")

            samples = []

            while True:
                data = receive(serial)

                print(data)
                respond(serial)

                samples.append(asdict(data))

                with open(filename, 'w') as file:
                    json.dump(samples, file, indent=4)
    except pyserial.SerialException:
        print("Invalid COM Port")
        return


async def infinite_print():
    while True:
        await asyncio.sleep(1)
        print('Hello')


async def in_thread(function):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, function)


async def main():
    baud_rate = 115200
    com_port: int = None

    try:
        com_port = sys.argv[1]
    except IndexError:
        print(f'Usage: {sys.argv[0]} [COM Port]', file=sys.stderr)
        return
    

    def serial_wrapped():
        serial_work(com_port, baud_rate)
    

    async with asyncio.TaskGroup() as task_group:
        task1 = task_group.create_task(
            in_thread(serial_wrapped)
        )

        task2 = task_group.create_task(
            infinite_print()
        )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye')
        os._exit(1)
