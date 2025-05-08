import json

def send_json(socket, data):
    socket.send(json.dumps(data).encode())

def recv_json(socket):
    return json.loads(socket.recv(4096).decode())
