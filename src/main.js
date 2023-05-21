let data = [];

const ctx = document.getElementById('myChart');

chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: data.map(row => row.x),
        datasets: [{
            label: 'Random data',
            data: data.map(row => row.y),
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
                    maxTicksLimit: 11,
                    callback: (label) => {
                        let seconds = label % 60;
                        let minutes = Math.floor(label / 60);
                        seconds = (seconds < 10 ? '0' : '') + seconds;
                        minutes = (minutes < 10 ? '0' : '') + minutes;
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

function updateChart() {
    const x = data.length;
    const y = Math.random();

    data.push({ x: x, y: y });
    // Sort the data in case the data was received out of order.
    data.sort((a, b) => { return a.x - b.x });

    chart.data.labels = data.map(row => row.x);
    chart.data.datasets[0].data = data.map(row => row.y);
    chart.update();
}

const socket = new WebSocket("ws://localhost:8765");

let intervalId;
let chartIntervalId;

socket.onopen = _ => {
    intervalId = setInterval(() => {
        socket.send("--Javascript");
    }, 1000);
};

socket.onmessage = event => {
    console.log(event.data);
};

socket.onclose = _ => {
    clearInterval(intervalId);
};

const startStopButton = document.getElementById('startStop');
startStopButton.addEventListener('click', event => {
    const state = event.target.innerText;
    if (state === 'Start') {
        event.target.innerText = 'Stop';
        socket.send('Start');
        console.log('Start');
        chartIntervalId = setInterval(updateChart, 300);
    } else {
        if (confirm('Do you really want to stop?')) {
            event.target.innerText = 'Start';
            socket.send('Stop');
            console.log('Stop');
            clearInterval(chartIntervalId);
        }
    }
});
