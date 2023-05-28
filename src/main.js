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

let visible_data = 'sound';

const ctx = document.getElementById('myChart');

chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: measurements[visible_data].map(row => row.time),
        datasets: [{
            label: 'Random data',
            data: measurements[visible_data].map(row => row.data),
            borderWidth: 1
        }]
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

let chartIntervalId;

socket.onopen = _ => {
    
};

socket.onmessage = event => {
    const received_data = JSON.parse(event.data);
    storeData(received_data);

    chart.data.labels = measurements[visible_data].map(row => row.time);
    chart.data.datasets[0].data = measurements[visible_data].map(row => row.data);
    chart.update();
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

function warnBeforeExiting(event) {
    event.preventDefault();
    return (event.returnValue = "");
};
