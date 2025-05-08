from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Set

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}  # sala → sockets
        self.message_id: Dict[str, int] = {}               # sala → id msg
        self.messages: Dict[str, Dict[int, Dict]] = {}     # sala → {id: msg}
        self.admins: Dict[str, Set[str]] = {}              # sala → admins
        self.creators: Dict[str, str] = {}                 # sala → creador

    async def connect(self, room: str, username: str, websocket: WebSocket):
        await websocket.accept()
        if room not in self.connections:
            self.connections[room] = []
            self.message_id[room] = 1
            self.messages[room] = {}
            self.admins[room] = {username}
            self.creators[room] = username
        self.connections[room].append(websocket)
        await self.send_history(room, websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if room in self.connections and websocket in self.connections[room]:
            self.connections[room].remove(websocket)

    async def send_history(self, room: str, websocket: WebSocket):
        for mid in sorted(self.messages[room]):
            msg = self.messages[room][mid]
            await websocket.send_json({
                "type": "msg",
                "id": mid,
                "from": msg["from"],
                "msg": msg["msg"]
            })

    async def broadcast(self, room: str, message: dict):
        for conn in self.connections.get(room, []):
            await conn.send_json(message)

    def is_admin(self, room: str, username: str) -> bool:
        return username in self.admins.get(room, set())

    def add_admin(self, room: str, username: str):
        self.admins[room].add(username)

    def delete_message(self, room: str, msg_id: int):
        if msg_id in self.messages[room]:
            del self.messages[room][msg_id]

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{room}/{username}")
async def websocket_endpoint(websocket: WebSocket, room: str, username: str):
    await manager.connect(room, username, websocket)
    try:
        await manager.broadcast(room, {"type": "info", "msg": f"{username} s'ha unit."})
        while True:
            data = await websocket.receive_json()

            if data["type"] == "msg":
                mid = manager.message_id[room]
                manager.messages[room][mid] = {"from": username, "msg": data["msg"]}
                await manager.broadcast(room, {
                    "type": "msg", "id": mid, "from": username, "msg": data["msg"]
                })
                manager.message_id[room] += 1

            elif data["type"] == "react":
                await manager.broadcast(room, {
                    "type": "reaction",
                    "id": data["id"],
                    "emoji": data["emoji"],
                    "from": username
                })

            elif data["type"] == "delete":
                if manager.is_admin(room, username):
                    manager.delete_message(room, data["id"])
                    await manager.broadcast(room, {
                        "type": "delete",
                        "id": data["id"],
                        "by": username
                    })

            elif data["type"] == "make_admin":
                if manager.creators[room] == username:
                    manager.add_admin(room, data["target"])
                    await manager.broadcast(room, {
                        "type": "info",
                        "msg": f"{data['target']} ara és admin (designat per {username})"
                    })

    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
        await manager.broadcast(room, {"type": "info", "msg": f"{username} ha sortit."})
