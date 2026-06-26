import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, plant_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[plant_id].add(websocket)

    async def disconnect(self, plant_id: int, websocket: WebSocket):
        async with self._lock:
            self._connections[plant_id].discard(websocket)
            if not self._connections[plant_id]:
                del self._connections[plant_id]

    async def broadcast(self, plant_id: int, data: dict[str, Any]):
        async with self._lock:
            sockets = list(self._connections.get(plant_id, set()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(plant_id, ws)


ws_manager = WebSocketManager()
