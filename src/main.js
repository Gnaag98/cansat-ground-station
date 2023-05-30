let measurements = {
    acceleration: [],
    gyroscope: [],
    distance: [],
    air: [],
    temperature: [],
    humidity: []
};

function getDatasetCategory() {
    switch (visibleData) {
        case 'acceleration':
        case 'gyroscope':
            return 'vector';
        case 'temperature':
        case 'humidity':
            return 'location';
        case 'air':
            return 'air';
        default:
            return 'default';
    }
}

let visibleData = 'distance';

const chartCanvas = document.getElementById('chart');

function getLabels() {
    return measurements[visibleData].map(row => row.time);
}

function createDataset(data, label) {
    return {
        data: data,
        borderWidth: 1,
        label: label
    }
}

function getDatasets() {
    const data = measurements[visibleData];
    switch (getDatasetCategory()) {
    case 'vector':
        return [
            createDataset(data.map(row => row.x), 'x'),
            createDataset(data.map(row => row.y), 'y'),
            createDataset(data.map(row => row.z), 'z'),
        ];
    case 'location':
        return [
            createDataset(data.map(row => row.outside), 'Outside'),
            createDataset(data.map(row => row.inside), 'Inside')
        ];
    case 'air':
        return [
            createDataset(data.map(row => row.air_quality), 'Air Quality'),
            createDataset(data.map(row => row.sound), 'Sound Level')
        ];
    default:
        return [
            createDataset(data.map(row => row.data))
        ];
    }
}

function getTitle() {
    associatedButton = document.getElementById(visibleData);
    return associatedButton.innerText;
}

function getUnit() {
    switch (visibleData) {
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
        spanGaps: false,
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

    const datasetCategory = getDatasetCategory();

    chart.options.plugins.legend.display = datasetCategory != 'default';
    chart.options.pointStyle = datasetCategory == 'location';

    chart.update();
}

function updateChart() {
    chart.data.labels = getLabels();

    switch (getDatasetCategory()) {
        case 'vector':
            chart.data.datasets[0].data = measurements[visibleData].map(row => row.x);
            chart.data.datasets[1].data = measurements[visibleData].map(row => row.y);
            chart.data.datasets[2].data = measurements[visibleData].map(row => row.z);
            break;
        case 'location':
            chart.data.datasets[0].data = measurements[visibleData].map(row => row.outside);
            chart.data.datasets[1].data = measurements[visibleData].map(row => row.inside);
            break;
        case 'air':
            chart.data.datasets[0].data = measurements[visibleData].map(row => row.air_quality);
            chart.data.datasets[1].data = measurements[visibleData].map(row => row.sound);
            break;
        default:
            chart.data.datasets[0].data = measurements[visibleData].map(row => row.data);
            break;
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

    measurements.acceleration.push({
        time: time,
        x: acceleration?.['x'] ?? null,
        y: acceleration?.['y'] ?? null,
        z: acceleration?.['z'] ?? null
    });

    measurements.gyroscope.push({
        time: time,
        x: gyroscope?.['x'] ?? null,
        y: gyroscope?.['y'] ?? null,
        z: gyroscope?.['z'] ?? null
    });

    measurements.distance.push({
        time: time,
        data: distance ?? null
    });

    measurements.air.push({
        time: time,
        air_quality: air_quality ?? null,
        sound: sound ?? null
    });

    measurements.temperature.push({
        time: time,
        outside: temperature_outside ?? null,
        inside: temperature_inside ?? null
    });

    measurements.humidity.push({
        time: time,
        outside: humidity_outside ?? null,
        inside: humidity_inside ?? null
    });

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

function sendCommand(action, value) {
    socket.send(`${action}:${value}`);
}

const startStopButton = document.getElementById('startStop');
const chartButtons = document.getElementsByClassName('chartButton');
const toggleButtons = document.getElementsByClassName('toggleButton');
const channelSelect = document.getElementById('channel');

startStopButton.addEventListener('click', event => {
    const state = event.target.innerText;
    if (state === 'Start') {
        addEventListener("beforeunload", warnBeforeExiting);
        event.target.innerText = 'Stop';
        sendCommand('Run', 1);
        channelSelect.setAttribute('disabled', '');
    } else {
        if (confirm('Do you really want to stop?')) {
            event.target.innerText = 'Start';
            sendCommand('Run', 0);
            channelSelect.removeAttribute('disabled');
            removeEventListener("beforeunload", warnBeforeExiting);
        }
    }
});

for (const button of chartButtons) {
    button.addEventListener('click', event => {
        visibleData = event.target.id;
        resetChart();
    });
}

function warnBeforeExiting(event) {
    event.preventDefault();
    return (event.returnValue = "");
};

for (const button of toggleButtons) {
    button.addEventListener('click', event => {
        let state;
        if (event.target.dataset.enabled == 'true') {
            event.target.dataset.enabled = false;
            state = 0;
        } else {
            event.target.dataset.enabled = true;
            state = 1;
        }
        
        sendCommand(event.target.dataset.sensor, state);
    });
}

channelSelect.addEventListener('change', event => {
    sendCommand('Radio Channel', parseInt(event.target.value));
});
