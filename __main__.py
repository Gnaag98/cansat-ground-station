from dataclasses import asdict
from functools import partial
import json
import os
import sys

from serial import Serial, SerialException
import asyncio
from websockets.server import serve, WebSocketServerProtocol

from src.relay import ReceiveState, Relay
from src.data import Data
from src.directory import Directory

samples = []


def sendCommand(serial: Serial, message: str):
    serial.write('01'.encode())

    if message == 'Start':
        serial.write(bytes([8, 1]))
    elif message == 'Stop':
        serial.write(bytes([8, 0]))


def respond(serial: Serial):
    serial.write('Thank you for the data\n'.encode())


def process_data(data: Data, directory: Directory):
    print(data)

    samples.append(asdict(data))

    directory.save(data)


def removeNoneFromDictionary(dictionary: dict):
    return {
        key: value for key, value in dictionary.items()
        if value is not None
    }


async def websocket_loop(websocket: WebSocketServerProtocol, serial: Serial):
    async for message in websocket:
        print(message)

        if (message == 'Start' or message == 'Stop'):
            sendCommand(serial, message)


async def serial_loop(websocket: WebSocketServerProtocol, serial: Serial, relay: Relay, directory: Directory):
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
                    await websocket.send(json.dumps(filtered_data))
                    
                    respond(serial)
            case ReceiveState.TEXT:
                text = relay.try_receive_text()
                if text:
                    print(text)
        await asyncio.sleep(0)


async def on_websocket_connect(websocket: WebSocketServerProtocol, serial: Serial):
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
