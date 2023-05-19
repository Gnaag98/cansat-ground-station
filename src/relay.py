from enum import Enum, IntEnum, auto
import time

from serial import Serial

from .data import Data, deserialize

_DATA_TIMEOUT_SECONDS = 0.1
_TEXT_TIMEOUT_SECONDS = 1
_HEADER_BYTES = b'01'


class ReceiveState(Enum):
    HEADER = auto()
    TYPE = auto()
    DATA = auto()
    TEXT = auto()


class MessageType(IntEnum):
    DATA = ord('0')
    TEXT = ord('1')


class Relay:
    def __init__(self, serial: Serial):
        self._serial = serial

        self._header_index = 0
        self._start_time: float
        self._receive_state = ReceiveState.HEADER
        self._incoming_text = ''


    @property
    def receive_state(self):
        return self._receive_state


    def _timeout(self, max_duration: str):
        if time.perf_counter() - self._start_time > max_duration:
            self._receive_state = ReceiveState.HEADER
            print('Timeout reached')
            return True
        else:
            return False


    def try_receive_header(self):
        if self._serial.in_waiting == 0:
            return
        
        byte = self._serial.read()[0]

        if byte == _HEADER_BYTES[self._header_index]:
            self._header_index += 1
            if self._header_index == len(_HEADER_BYTES):
                self._receive_state = ReceiveState.TYPE
                self._header_index = 0
        else:
            self._header_index = 0
            print(f"Incorrect start byte: '{chr(byte)}' = {byte}.")


    def try_receive_type(self):
        if self._serial.in_waiting == 0:
            return
        
        byte = self._serial.read()[0]

        match byte:
            case MessageType.DATA:
                self._receive_state = ReceiveState.DATA
            case MessageType.TEXT:
                self._receive_state = ReceiveState.TEXT
                self._incoming_text = ''
            case _:
                self._receive_state = ReceiveState.HEADER
                print('Incorrect message type.')
                return

        self._start_time = time.perf_counter()

    def try_receive_data(self) -> Data | None:
        if self._timeout(_DATA_TIMEOUT_SECONDS):
            return None

        if self._serial.in_waiting >= 30:
            serialized = self._serial.read(30)
            data = deserialize(serialized)
            self._receive_state = ReceiveState.HEADER
            return data
        else:
            return None


    def try_receive_text(self) -> str | None:
        if self._timeout(_TEXT_TIMEOUT_SECONDS):
            return None

        if self._serial.in_waiting > 0:
            byte = self._serial.read()[0]
            character = chr(byte)
            if character == '\n':
                self._receive_state = ReceiveState.HEADER
                return self._incoming_text
            else:
                self._incoming_text += character
        return None
