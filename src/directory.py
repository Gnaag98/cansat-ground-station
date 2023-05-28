import csv
from datetime import datetime
from pathlib import Path

from .data import Vector, Data


class Directory:
    def __init__(self):
        date_string = datetime.today().strftime("%Y-%m-%d_%H.%M.%S")
        self._directory = Path('data', date_string)
        self._directory.mkdir()
        
        self._initialize_vector_file(self._directory / 'acceleration.csv')
        self._initialize_vector_file(self._directory / 'gyroscope.csv')
        self._initialize_number_file(self._directory / 'temperature_outside.csv')
        self._initialize_number_file(self._directory / 'distance.csv')
        self._initialize_number_file(self._directory / 'air_quality.csv')
        self._initialize_number_file(self._directory / 'sound.csv')
        self._initialize_number_file(self._directory / 'temperature_inside.csv')
        self._initialize_number_file(self._directory / 'humidity_inside.csv')
        self._initialize_number_file(self._directory / 'humidity_outside.csv')


    def save(self, data: Data):
        self._save_vector(self._directory / 'acceleration.csv', data.time, data.acceleration)
        self._save_vector(self._directory / 'gyroscope.csv', data.time, data.gyroscope)
        self._save_number(self._directory / 'temperature_outside.csv', data.time, data.temperature_outside)
        self._save_number(self._directory / 'distance.csv', data.time, data.distance)
        self._save_number(self._directory / 'air_quality.csv', data.time, data.air_quality)
        self._save_number(self._directory / 'sound.csv', data.time, data.sound)
        self._save_number(self._directory / 'temperature_inside.csv', data.time, data.temperature_inside)
        self._save_number(self._directory / 'humidity_inside.csv', data.time, data.humidity_inside)
        self._save_number(self._directory / 'humidity_outside.csv', data.time, data.humidity_outside)


    def _initialize_vector_file(self, path: Path):
        with path.open('w', newline='') as file:
            fieldnames = ['time', 'x', 'y', 'z']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()


    def _initialize_number_file(self, path: Path):
        with path.open('w', newline='') as file:
            fieldnames = ['time', 'data']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()


    def _save_vector(self, path: Path, time: int, vector: Vector):
        with path.open('a', newline='') as file:
            fieldnames = ['time', 'x', 'y', 'z']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow({ 'time': time, 'x': vector.x, 'y': vector.y, 'z': vector.z })


    def _save_number(self, path: Path, time: int, number: int | float):
        with path.open('a', newline='') as file:
            fieldnames = ['time', 'data']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow({ 'time': time, 'data': number })
