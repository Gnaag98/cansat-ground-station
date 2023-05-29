let measurements = {
    acceleration: [],
    gyroscope: [],
    distance: [],
    air_quality: [],
    sound: [],
    temperature: [],
    humidity: []
};

function getDatasetCount() {
    switch (visibleData) {
        case 'acceleration':
        case 'gyroscope':
            return 3;
        case 'temperature':
        case 'humidity':
            return 2;
        default:
            return 1;
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
    switch (getDatasetCount()) {
    case 1:
        return [
            createDataset(data.map(row => row.data))
        ];
    case 2:
        return [
            createDataset(data.map(row => row.outside), 'Outside'),
            createDataset(data.map(row => row.inside), 'Inside')
        ];
    case 3:
        return [
            createDataset(data.map(row => row.x), 'x'),
            createDataset(data.map(row => row.y), 'y'),
            createDataset(data.map(row => row.z), 'z'),
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

    switch (getDatasetCount()) {
    case 1:
        chart.options.plugins.legend.display = false;
        break;
    case 2:
    case 3:
        chart.options.plugins.legend.display = true;
        break;
    }

    chart.update();
}

function updateChart() {
    chart.data.labels = getLabels();

    switch (getDatasetCount()) {
    case 1:
        chart.data.datasets[0].data = measurements[visibleData].map(row => row.data);
        break;
    case 2:
        chart.data.datasets[0].data = measurements[visibleData].map(row => row.outside);
        chart.data.datasets[1].data = measurements[visibleData].map(row => row.inside);
        break;
    case 3:
        chart.data.datasets[0].data = measurements[visibleData].map(row => row.x);
        chart.data.datasets[1].data = measurements[visibleData].map(row => row.y);
        chart.data.datasets[2].data = measurements[visibleData].map(row => row.z);
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
        x: acceleration['x'] ?? null,
        y: acceleration['y'] ?? null,
        z: acceleration['z'] ?? null
    });

    measurements.gyroscope.push({
        time: time,
        x: gyroscope['x'] ?? null,
        y: gyroscope['y'] ?? null,
        z: gyroscope['z'] ?? null
    });

    measurements.sound.push({
        time: time,
        data: sound ?? null
    });

    measurements.distance.push({
        time: time,
        data: distance ?? null
    });

    measurements.air_quality.push({
        time: time,
        data: air_quality ?? null
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
        if (button.classList.contains('off')) {
            state = 1;
            button.classList.remove('off');
        } else {
            state = 0;
            button.classList.add('off');
        }
        sendCommand(event.target.innerText, state);
    });
}

channelSelect.addEventListener('change', event => {
    sendCommand('Radio Channel', parseInt(event.target.value));
});
