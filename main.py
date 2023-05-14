import sys
import time

import serial as pyserial


def greet(serial: pyserial.Serial):
    serial.write('Hello'.encode())


def listen(serial: pyserial.Serial):
    while True:
        if serial.in_waiting > 0:
            character = serial.read().decode()
            print(character, end='')



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
        #greet()
        #time.sleep(1)
        listen(serial)


if __name__ == '__main__':
    main()