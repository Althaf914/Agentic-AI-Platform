"""
WebSocket router — real-time workflow event streaming with graceful disconnect handling.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections grouped by workflow_id."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        """Accept and register a WebSocket connection for a workflow."""
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
        logger.info(f"WebSocket connected for workflow {workflow_id}")

    def disconnect(self, workflow_id: str, websocket: WebSocket):
        """Remove a WebSocket connection from the active list."""
        if workflow_id in self.active_connections:
            try:
                self.active_connections[workflow_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")

    async def broadcast(self, workflow_id: str, message):
        """Send a message to all connections watching a specific workflow."""
        if workflow_id not in self.active_connections:
            return

        import json
        text = json.dumps(message) if isinstance(message, dict) else str(message)

        dead = []
        for ws in self.active_connections[workflow_id]:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(workflow_id, ws)


# Singleton manager instance — imported by workflow_engine/events.py
manager = ConnectionManager()


@router.websocket("/ws/{workflow_id}")
async def workflow_websocket(workflow_id: str, websocket: WebSocket):
    """WebSocket endpoint for real-time workflow event streaming."""
    await manager.connect(workflow_id, websocket)
    try:
        while True:
            # Keep connection alive — receive pings or any client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(workflow_id, websocket)
    except Exception:
        manager.disconnect(workflow_id, websocket)
