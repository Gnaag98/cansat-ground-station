const socket = new WebSocket("ws://localhost:8765");

socket.onopen = _ => {
    socket.send("Welcome");
};

socket.onmessage = event => {
    console.log(event.data);
};
