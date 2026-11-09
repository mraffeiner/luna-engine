import asyncio
import json
import logging
from typing import Any, Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Use asyncio.Lock as all operations on connections should happen within the async event loop
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection and adds it to the list."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected: {websocket.client}. Total: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection from the list."""
        async with self._lock:
            # Check if connection still exists before removing
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(
                    f"WebSocket disconnected: {websocket.client}. Total: {len(self.active_connections)}"
                )
            # else: connection might have already been removed by another task (e.g., broadcast error)

    async def broadcast(self, message: Dict[str, Any]):
        """Sends a JSON message to all active WebSocket connections."""
        message_json = json.dumps(message)
        # Get a snapshot of connections under lock to avoid modification during iteration
        async with self._lock:
            connections_to_broadcast = self.active_connections[:]

        # Use asyncio.gather for potentially faster broadcasting, but handle errors individually
        results = await asyncio.gather(
            *(
                self._send_to_connection(connection, message_json)
                for connection in connections_to_broadcast
            ),
            return_exceptions=True,
        )

        # Process results to disconnect failed connections
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                connection = connections_to_broadcast[i]
                logger.warning(
                    f"Broadcast failed for {connection.client}: {result}. Disconnecting."
                )
                # Disconnect outside the gather call
                await self.disconnect(connection)

    async def _send_to_connection(self, connection: WebSocket, message_json: str):
        """Helper to send message to a single connection, raising exception on failure."""
        # This ensures that if send_text fails, the exception propagates up to the gather call
        await connection.send_text(message_json)
