import socket
import threading
from common import send_json, recv_json

HOST = 'localhost'
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

name = input("Introdueix el teu nom: ")
send_json(client, {"name": name})

def listen_server():
    while True:
        data = recv_json(client)
        if data["type"] == "msg":
            print(f"[{data['room']}] {data['from']}: {data['msg']}")
        elif data["type"] == "info":
            print(f"[INFO] {data['msg']}")

threading.Thread(target=listen_server, daemon=True).start()

while True:
    cmd = input("Comanda (join, send, delete, make_admin): ").strip()
    if cmd == "join":
        room = input("Nom de la sala: ")
        send_json(client, {"type": "join", "room": room})
    elif cmd == "send":
        room = input("Sala: ")
        msg = input("Missatge: ")
        send_json(client, {"type": "msg", "room": room, "msg": msg})
    elif cmd == "delete":
        room = input("Sala: ")
        msg = input("Missatge a esborrar exactament: ")
        send_json(client, {"type": "delete", "room": room, "msg": msg})
    elif cmd == "make_admin":
        room = input("Sala: ")
        target = input("Usuari a fer admin: ")
        send_json(client, {"type": "make_admin", "room": room, "target": target})
