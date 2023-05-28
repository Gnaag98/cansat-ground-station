let measurements = {
    acceleration: [],
    gyroscope: [],
    distance: [],
    air_quality: [],
    sound: [],
    temperature: [],
    humidity: []
};

let visible_data = 'distance';

const chartCanvas = document.getElementById('chart');

function getLabels() {
    return measurements[visible_data].map(row => row.time);
}

function createDataset(data, label) {
    return {
        data: data,
        borderWidth: 1,
        label: label
    }
}

function getDatasets() {
    const data = measurements[visible_data];
        if (data.length > 0) {
            if (data[0]['data']) {
                return [
                    createDataset(data.map(row => row.data))
                ];
            } else if (data[0]['x']) {
                return [
                    createDataset(data.map(row => row.x), 'x'),
                    createDataset(data.map(row => row.y), 'y'),
                    createDataset(data.map(row => row.z), 'z')
                ];
            } else {
                return [
                    createDataset(data.map(row => row.outside), 'Outside'),
                    createDataset(data.map(row => row.inside), 'Inside')
                ];
            }
        } else {
            return [
                createDataset([])
            ];
        }
}

function getTitle() {
    associatedButton = document.getElementById(visible_data);
    return associatedButton.innerText;
}

function getUnit() {
    switch (visible_data) {
        case 'acceleration':
            return 'm/s^2';
        case 'gyroscope':
            return '°/s';
        case 'distance':
            return 'cm';
        case 'temperature':
            return '°C';
        case 'humidity':
            return '%RH';
        default:
            return '';
    }
}

chart = new Chart(chartCanvas, {
    type: 'line',
    data: {
        labels: getLabels(),
        datasets: getDatasets()
    },
    options: {
        animation: true,
        pointStyle: false,
        maintainAspectRatio: false,
        scales: {
            x: {
                ticks: {
                    display: true,
                    maxTicksLimit: 11,
                    callback: function(label) {
                        label = this.getLabelForValue(label);
                        let minutes = Math.floor(label / 1000 / 60);
                        let seconds = Math.floor(label / 1000 % 60);
                        minutes = minutes.toString().padStart(2, '0');
                        seconds = seconds.toString().padStart(2, '0');
                        return `T+${minutes}:${seconds}`;
                    }
                }
            },
            y: {
                ticks: {
                    callback: function(label) {
                        label = this.getLabelForValue(label);
                        return `${label} ${getUnit()}`;
                    }
                }
            }
        },
        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: getTitle()
            }
        }
    }
});

function resetChart() {
    chart.data.labels = getLabels();
    chart.data.datasets = getDatasets();
    chart.options.plugins.title.text = getTitle();

    if (measurements[visible_data].length > 0) {
        if (measurements[visible_data][0]['data']) {
            chart.options.plugins.legend.display = false;
        } else {
            chart.options.plugins.legend.display = true;
        }
    }

    chart.update();
}

function updateChart() {
    if (measurements[visible_data].length > 0) {
        chart.data.labels = getLabels();
        if (measurements[visible_data][0]['data']) {
            chart.data.datasets[0].data = measurements[visible_data].map(row => row.data);
        } else if (measurements[visible_data][0]['x']) {
            chart.data.datasets[0].data = measurements[visible_data].map(row => row.x);
            chart.data.datasets[1].data = measurements[visible_data].map(row => row.y);
            chart.data.datasets[2].data = measurements[visible_data].map(row => row.z);
        } else {
            chart.data.datasets[0].data = measurements[visible_data].map(row => row.outside);
            chart.data.datasets[1].data = measurements[visible_data].map(row => row.inside);
        }

    } else {
        chart.data.labels = [];
        chart.data.datasets = [];
    }
    chart.update();
}

function storeData(data) {
    const time = data['time'];
    const acceleration = data['acceleration'];
    const gyroscope = data['gyroscope'];
    const temperature_outside = data['temperature_outside'];
    const temperature_inside = data['temperature_inside'];
    const sound = data['sound'];
    const distance = data['distance'];
    const air_quality = data['air_quality'];
    const humidity_inside = data['humidity_inside'];
    const humidity_outside = data['humidity_outside'];
    
    if (acceleration) {
        measurements.acceleration.push({
            time: time,
            x: acceleration['x'],
            y: acceleration['y'],
            z: acceleration['z']
        });
    }
    
    if (gyroscope) {
        measurements.gyroscope.push({
            time: time,
            x: gyroscope['x'],
            y: gyroscope['y'],
            z: gyroscope['z']
        });
    }

    if (sound) {
        measurements.sound.push({
            time: time,
            data: sound
        });
    }

    if (distance) {
        measurements.distance.push({
            time: time,
            data: distance
        });
    }

    if (air_quality) {
        measurements.air_quality.push({
            time: time,
            data: air_quality
        });
    }

    if (temperature_outside || temperature_inside) {
        measurements.temperature.push({
            time: time,
            outside: temperature_outside ?? null,
            inside: temperature_inside ?? null
        });
    }

    if (humidity_outside || humidity_inside) {
        measurements.humidity.push({
            time: time,
            outside: humidity_outside ?? null,
            inside: humidity_inside ?? null
        });
    }

    // Sort the data in case the data was received out of order.
    for (const measurement_type in measurements) {
        measurements[measurement_type].sort((a, b) => { return a.time - b.time });
    }
}

const socket = new WebSocket("ws://localhost:8765");

socket.onopen = _ => {
    
};

socket.onmessage = event => {
    const received_data = JSON.parse(event.data);
    storeData(received_data);

    updateChart();
};

socket.onclose = _ => {
    
};

const startStopButton = document.getElementById('startStop');
startStopButton.addEventListener('click', event => {
    const state = event.target.innerText;
    if (state === 'Start') {
        addEventListener("beforeunload", warnBeforeExiting);
        event.target.innerText = 'Stop';
        socket.send('Run:1');
    } else {
        if (confirm('Do you really want to stop?')) {
            event.target.innerText = 'Start';
            socket.send('Run:0');
            removeEventListener("beforeunload", warnBeforeExiting);
        }
    }
});

const chartButtons = document.getElementsByClassName('chartButton');
for (const button of chartButtons) {
    button.addEventListener('click', event => {
        visible_data = event.target.id;
        resetChart();
    });
}

function warnBeforeExiting(event) {
    event.preventDefault();
    return (event.returnValue = "");
};

const toggleButtons = document.getElementsByClassName('toggleButton');
for (const button of toggleButtons) {
    button.addEventListener('click', event => {
        let state;
        if (button.classList.contains('off')) {
            state = 1;
            button.classList.remove('off');
        } else {
            state = 0;
            button.classList.add('off');
        }
        socket.send(`${event.target.innerText}:${state}`);
    });
}