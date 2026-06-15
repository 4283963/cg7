import asyncio
import json
from typing import List, Set
from datetime import datetime


class WebSocketManager:
    def __init__(self):
        self._connections: Set = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket):
        await self._lock.acquire()
        try:
            self._connections.add(websocket)
        finally:
            self._lock.release()
        await websocket.accept()

    async def disconnect(self, websocket):
        await self._lock.acquire()
        try:
            self._connections.discard(websocket)
        finally:
            self._lock.release()

    async def broadcast(self, message: dict):
        dead_connections = set()
        message_json = json.dumps(message, default=str)
        
        await self._lock.acquire()
        try:
            connections = list(self._connections)
        finally:
            self._lock.release()

        for ws in connections:
            try:
                await ws.send_text(message_json)
            except Exception:
                dead_connections.add(ws)

        if dead_connections:
            await self._lock.acquire()
            try:
                self._connections -= dead_connections
            finally:
                self._lock.release()

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
