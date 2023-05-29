from __future__ import annotations

from dataclasses import dataclass
from struct import unpack

dataSize = 27
dropDataSize = 16


@dataclass
class Vector:
    x: float
    y: float
    z: float


    def __sub__(self, other: Vector):
        return Vector(
            x=self.x - other.x,
            y=self.y - other.y,
            z=self.z - other.z
        )


@dataclass
class Data:
    acceleration: Vector
    gyroscope: Vector
    time: int
    temperature_outside: float
    distance: int
    air_quality: int
    sound: int
    temperature_inside: int
    humidity_inside: int
    humidity_outside: int


@dataclass
class DropData:
    acceleration: Vector
    gyroscope: Vector
    time: int


# Missing data sent as -1 will be changed to None.
# Not all sensors return errors.
def convertNegativeToNone(number: int | float) -> int | float | None:
    if number < 0:
        return None
    else:
        return number


# Missing data sent as 255 will be changed to None.
# Not all sensors return errors.
def convert255ToNone(number: int) -> int | None:
    if number == 255:
        return None
    else:
        return number



# The CanSat saves space by rounding off floats to three decimals and storing
# the result as an int. It does this by multiplying the floats by 1000.
def convertIntToFloat(number: int) -> float:
    return number / 1000


def convertVector(x: int, y: int, z: int) -> Vector:
    x = convertIntToFloat(x)
    y = convertIntToFloat(y)
    z = convertIntToFloat(z)

    return Vector(x, y, z)


def deserializeData(serialized: bytes) -> Data:
    deserialized = unpack('<hhhhhhLhhhhBBB', serialized)

    data = Data(
        acceleration = convertVector(*deserialized[:3]),
        gyroscope = convertVector(*deserialized[3:6]),
        time = deserialized[6],
        temperature_outside = convertNegativeToNone(convertIntToFloat(deserialized[7])),
        distance = convertNegativeToNone(deserialized[8]),
        air_quality = deserialized[9],
        sound = deserialized[10],
        temperature_inside = convert255ToNone(deserialized[11]),
        humidity_inside = convert255ToNone(deserialized[12]),
        humidity_outside = convert255ToNone(deserialized[13])
    )

    return data


def deserializeDropData(serialized: bytes) -> DropData:
    deserialized = unpack('<hhhhhhL', serialized)

    data = DropData(
        acceleration = convertVector(*deserialized[:3]),
        gyroscope = convertVector(*deserialized[3:6]),
        time = deserialized[6],
    )

    return data
