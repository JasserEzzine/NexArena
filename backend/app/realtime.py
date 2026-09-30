import asyncio
from fastapi import WebSocket


class Hub:
    def __init__(self):
        self.agents: dict[str, WebSocket] = {}
        self.dashboards: set[WebSocket] = set()
        self.locks: dict[str, asyncio.Lock] = {}

    async def publish(self, event="refresh", data=None):
        for ws in list(self.dashboards):
            try:
                await asyncio.wait_for(ws.send_json({"event": event, "data": data}), 2)
            except Exception:
                self.dashboards.discard(ws)

    async def command(self, node_id, payload):
        if node_id not in self.agents:
            return False
        try:
            async with self.locks.setdefault(node_id, asyncio.Lock()):
                await asyncio.wait_for(self.agents[node_id].send_json(payload), 3)
            return True
        except Exception:
            return False


hub = Hub()
