from dataclasses import dataclass, asdict
import json
from struct import unpack
import sys
from datetime import datetime

import serial as pyserial


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


def greet(serial: pyserial.Serial):
    serial.write('Thank you for the data\n'.encode())


def listen(serial: pyserial.Serial):
    is_waiting = True
    now = datetime.today()
    filename = now.strftime("data/data_%Y-%m-%d_%H.%M.%S.txt")

    samples = []

    while True:
        while is_waiting:
            if serial.in_waiting > 0:
                byte = serial.read()
                if chr(byte[0]) == '0':
                    print('Message incoming: ', end='')
                    is_waiting = False
                else:
                    print(chr(byte[0]), end='')

        while not is_waiting:
            if serial.in_waiting >= 30:
                bytes = serial.read(30)
                data = deserialize(bytes)
                print(data)

                greet(serial)

                samples.append(asdict(data))

                with open(filename, 'w') as file:
                    json.dump(samples, file, indent=4)

                is_waiting = True


def main():
    baud_rate = 115200
    com_port: int = None

    try:
        com_port = sys.argv[1]
    except IndexError:
        print(f'Usage: {sys.argv[0]} [COM Port]', file=sys.stderr)
    except ValueError:
        print("Invalid COM Port")
    
    with pyserial.Serial(port=com_port, baudrate=baud_rate, timeout=0) as serial:
        listen(serial)


if __name__ == '__main__':
    main()
