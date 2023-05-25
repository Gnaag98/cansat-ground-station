from dataclasses import dataclass
from struct import unpack

dataSize = 21


@dataclass
class Acceleration:
    x: float
    y: float
    z: float


@dataclass
class Data:
    acceleration: Acceleration
    time: int
    temperature_outside: float
    sound: int
    distance: int
    air_quality: int
    temperature_inside: int
    humidity_inside: int
    humidity_outside: int


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
def convertIntToFloat(number: int):
    return number / 1000


def convertAcceleration(x: int, y: int, z: int):
    x = convertIntToFloat(x)
    y = convertIntToFloat(y)
    z = convertIntToFloat(z)

    if x and y and z:
        return Acceleration(x, y, z)
    else:
        return None


def deserialize(serialized: bytes):
    deserialized = unpack('<hhhLhhhhBBB', serialized)

    data = Data(
        acceleration = convertAcceleration(*deserialized[:3]),
        time = deserialized[3],
        temperature_outside = convertNegativeToNone(convertIntToFloat(deserialized[4])),
        sound = deserialized[5],
        distance = convertNegativeToNone(deserialized[6]),
        air_quality = deserialized[7],
        temperature_inside = convert255ToNone(deserialized[8]),
        humidity_inside = convert255ToNone(deserialized[9]),
        humidity_outside = convert255ToNone(deserialized[10])
    )

    return data
