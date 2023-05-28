let measurements = {
    acceleration: [],
    gyroscope: [],
    temperature_outside: [],
    sound: [],
    distance: [],
    air_quality: [],
    temperature_inside: [],
    humidity_inside: [],
    humidity_outside: []
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
        } else {
            return [
                createDataset(data.map(row => row.x), 'x'),
                createDataset(data.map(row => row.y), 'y'),
                createDataset(data.map(row => row.z), 'z')
            ];
        }
    } else {
        return [
            createDataset([])
        ];
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
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

function resetChart() {
    chart.data.labels = getLabels();
    chart.data.datasets = getDatasets();

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
        } else {
            chart.data.datasets[0].data = measurements[visible_data].map(row => row.x);
            chart.data.datasets[1].data = measurements[visible_data].map(row => row.y);
            chart.data.datasets[2].data = measurements[visible_data].map(row => row.z);
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

    if (temperature_outside) {
        measurements.temperature_outside.push({
            time: time,
            data: temperature_outside
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

    if (temperature_inside) {
        measurements.temperature_inside.push({
            time: time,
            data: temperature_inside
        });
    }

    if (humidity_inside) {
        measurements.humidity_inside.push({
            time: time,
            data: humidity_inside
        });
    }

    if (humidity_outside) {
        measurements.humidity_outside.push({
            time: time,
            data: humidity_outside
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
        socket.send('Start');
    } else {
        if (confirm('Do you really want to stop?')) {
            event.target.innerText = 'Start';
            socket.send('Stop');
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
