from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    def connect(self, user_id: int, websocket: WebSocket) -> None:
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def send_to_users(self, user_ids: set[int], payload: dict) -> None:
        for user_id in user_ids:
            for websocket in list(self._connections.get(user_id, set())):
                try:
                    await websocket.send_json(payload)
                except RuntimeError:
                    self.disconnect(user_id, websocket)


websocket_manager = ConnectionManager()
