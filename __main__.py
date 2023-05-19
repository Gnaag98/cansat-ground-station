from dataclasses import dataclass, asdict
from enum import Enum, IntEnum, auto
from functools import partial
import json
import os
from struct import unpack
import sys
from datetime import datetime
import time

from serial import Serial, SerialException
import asyncio
from websockets.server import serve, WebSocketServerProtocol

from src.relay import ReceiveState, Relay
from src.data import Data

samples = []


def respond(serial: Serial):
    serial.write('Thank you for the data\n'.encode())


def process_data(data: Data, filename: str, serial: Serial):
    print(data)
    respond(serial)

    samples.append(asdict(data))

    with open(filename, 'w') as file:
        json.dump(samples, file, indent=4)


async def websocket_loop(websocket: WebSocketServerProtocol):
    async for message in websocket:
        print(message)


async def serial_loop(websocket: WebSocketServerProtocol, serial: Serial, relay: Relay, filename: str):
    while websocket.open:
        match relay.receive_state:
            case ReceiveState.HEADER:
                relay.try_receive_header()
            case ReceiveState.TYPE:
                relay.try_receive_type()
            case ReceiveState.DATA:
                data = relay.try_receive_data()
                if data:
                    process_data(data, filename, serial)
            case ReceiveState.TEXT:
                text = relay.try_receive_text()
                if text:
                    print(text)
        await asyncio.sleep(0)


async def on_websocket_connect(websocket: WebSocketServerProtocol, serial: Serial):
    # Code here will run when a websocket client connects.
    filename = datetime.today().strftime("data/data_%Y-%m-%d_%H.%M.%S.txt")

    relay = Relay(serial)

    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(serial_loop(websocket, serial, relay, filename))

        await websocket_loop(websocket)


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
