let socket = null;

function join() {
    const user = document.getElementById("username").value;
    const room = document.getElementById("room").value;
    if (!user || !room) {
        alert("Escriu nom i sala");
        return;
    }

    socket = new WebSocket(`ws://${location.host}/ws/${room}/${user}`);

    socket.onopen = () => {
        document.getElementById("chat").style.display = "block";
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const msgBox = document.getElementById("messages");

        if (data.type === "msg") {
            msgBox.innerHTML += `<div id="msg-${data.id}">[#${data.id}] <b>${data.from}:</b> ${data.msg}</div>`;
        } else if (data.type === "reaction") {
            msgBox.innerHTML += `<div>🔁 Reacció a #${data.id}: ${data.emoji} (${data.from})</div>`;
        } else if (data.type === "info") {
            msgBox.innerHTML += `<div><i>${data.msg}</i></div>`;
        } else if (data.type === "delete") {
            const el = document.getElementById(`msg-${data.id}`);
            if (el) {
                el.innerHTML = `<i>Missatge esborrat per ${data.by}</i>`;
                el.style.color = "#888";
            }
        }
        msgBox.scrollTop = msgBox.scrollHeight;
    };

    socket.onerror = (e) => {
        console.error("WebSocket error:", e);
        alert("Error en la connexió");
    };
}


function sendMsg() {
    const msg = document.getElementById("input").value;
    if (msg && socket) {
        socket.send(JSON.stringify({ type: "msg", msg }));
        document.getElementById("input").value = "";
    }
}

function sendReaction() {
    const id = document.getElementById("react_id").value;
    const emoji = document.getElementById("emoji").value;
    if (id && emoji && socket) {
        socket.send(JSON.stringify({ type: "react", id: parseInt(id), emoji }));
    }
}

function sendDelete() {
    const id = prompt("ID del missatge a esborrar:");
    if (id) {
        socket.send(JSON.stringify({ type: "delete", id: parseInt(id) }));
    }
}

function makeAdmin() {
    const target = prompt("Usuari a fer admin:");
    if (target) {
        socket.send(JSON.stringify({ type: "make_admin", target }));
    }
}

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const msgBox = document.getElementById("messages");
    if (data.type === "msg") {
        msgBox.innerHTML += `<div id="msg-${data.id}">[#${data.id}] <b>${data.from}:</b> ${data.msg}</div>`;
    } else if (data.type === "reaction") {
        msgBox.innerHTML += `<div>🔁 Reacció a #${data.id}: ${data.emoji} (${data.from})</div>`;
    } else if (data.type === "info") {
        msgBox.innerHTML += `<div><i>${data.msg}</i></div>`;
    } else if (data.type === "delete") {
        const el = document.getElementById(`msg-${data.id}`);
        if (el) el.innerHTML = `<i>Missatge esborrat per ${data.by}</i>`;
    }
    
    msgBox.scrollTop = msgBox.scrollHeight;
};

