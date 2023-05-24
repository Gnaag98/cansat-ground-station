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


# The CanSat saves space by rounding off floats to three decimals and storing
# the result as an int. It does this by multiplying the floats by 1000.
def convertIntToFloat(number: int):
    return number / 1000


def convertAcceleration(x: int, y: int, z: int):
    return Acceleration(
        x=convertIntToFloat(x),
        y=convertIntToFloat(y),
        z=convertIntToFloat(z)
    )


def deserialize(serialized: bytes):
    deserialized = unpack('<hhhLhhhhBBB', serialized)

    acceleration = convertAcceleration(*deserialized[:3])
    time = deserialized[3]
    temperature_outside = convertIntToFloat(deserialized[4])
    remaining_variables = deserialized[5:]

    return Data(acceleration, time, temperature_outside, *remaining_variables)
