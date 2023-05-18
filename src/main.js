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