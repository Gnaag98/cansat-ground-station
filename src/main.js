const socket = new WebSocket("ws://localhost:8765");

let intervalId;

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
    } else {
        event.target.innerText = 'Start';
        socket.send('Stop');
        console.log('Stop');
    }
});
