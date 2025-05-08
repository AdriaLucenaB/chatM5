import socket
import threading
from common import send_json, recv_json

HOST = 'localhost'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}  # socket: {"name": str, "rooms": set()}
rooms = {}    # room_name: {"members": set(socket), "admins": set(socket), "history": list[dict]}

lock = threading.Lock()

def broadcast(room, message):
    for client in rooms[room]["members"]:
        send_json(client, message)

def handle_client(client_socket):
    try:
        user = recv_json(client_socket)
        with lock:
            clients[client_socket] = {"name": user["name"], "rooms": set()}
        send_json(client_socket, {"type": "info", "msg": f"Benvingut/da {user['name']}!"})

        while True:
            data = recv_json(client_socket)
            if data["type"] == "join":
                room = data["room"]
                with lock:
                    if room not in rooms:
                        rooms[room] = {"members": set(), "admins": set(), "history": []}
                        rooms[room]["admins"].add(client_socket)
                    rooms[room]["members"].add(client_socket)
                    clients[client_socket]["rooms"].add(room)

                    for msg in rooms[room]["history"]:
                        send_json(client_socket, msg)

                broadcast(room, {"type": "msg", "room": room, "from": "Sistema", "msg": f"{clients[client_socket]['name']} s'ha unit."})

            elif data["type"] == "msg":
                room = data["room"]
                msg_obj = {"type": "msg", "room": room, "from": clients[client_socket]["name"], "msg": data["msg"]}
                with lock:
                    rooms[room]["history"].append(msg_obj)
                broadcast(room, msg_obj)

            elif data["type"] == "delete" and data["room"] in clients[client_socket]["rooms"]:
                room = data["room"]
                if client_socket in rooms[room]["admins"]:
                    with lock:
                        rooms[room]["history"] = [m for m in rooms[room]["history"] if m["msg"] != data["msg"]]
                    broadcast(room, {"type": "info", "msg": f"L'admin ha esborrat un missatge."})

            elif data["type"] == "make_admin":
                room = data["room"]
                target = data["target"]
                with lock:
                    if client_socket in rooms[room]["admins"]:
                        for s, u in clients.items():
                            if u["name"] == target:
                                rooms[room]["admins"].add(s)
                                send_json(s, {"type": "info", "msg": f"Ara ets administrador de {room}."})
                                break

    except:
        pass
    finally:
        with lock:
            for room in clients.get(client_socket, {}).get("rooms", []):
                if client_socket in rooms[room]["members"]:
                    rooms[room]["members"].remove(client_socket)
        client_socket.close()

print(f"Servidor escoltant a {HOST}:{PORT}")
while True:
    client_socket, addr = server.accept()
    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
