from dataclasses import dataclass
from struct import unpack


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
