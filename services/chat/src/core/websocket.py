import logging
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    # Depends, # Keep commented in case needed elsewhere
)

# Import the dependency getter and the manager type
# from .dependencies import get_ws_manager # No longer needed for this endpoint
from .websocket_manager import ConnectionManager
from ..config import STATE_WS_MANAGER  # Import the state key

logger = logging.getLogger(__name__)

# Create an APIRouter instance for WebSocket endpoints
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    # ws_manager: ConnectionManager = Depends(get_ws_manager), # Removed dependency injection
):
    """Handles incoming WebSocket connections for broadcasting chat messages."""
    # Retrieve the manager directly from the application state
    ws_manager: ConnectionManager = getattr(websocket.app.state, STATE_WS_MANAGER, None)
    if not ws_manager or not isinstance(ws_manager, ConnectionManager):
        # Handle case where manager isn't initialized or has wrong type
        client_addr = (
            f"{websocket.client.host}:{websocket.client.port}"
            if websocket.client
            else "unknown"
        )
        logger.error(
            f"ConnectionManager not found or invalid in app state during WebSocket connection from {client_addr}"
        )
        await websocket.close(code=1011)  # Internal error
        return

    client_host = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "unknown"
    client_addr = f"{client_host}:{client_port}"

    await ws_manager.connect(websocket)
    logger.info(f"WebSocket connected: {client_addr}")
    try:
        while True:
            # Keep connection alive. Handle potential client messages here if needed.
            # If client sends data, it will be received here.
            # If only broadcasting, this loop just waits for disconnect.
            data = await websocket.receive_text()
            # logger.debug(f"Received keep-alive/message from {client_addr}: {data}")
            # If you need to react to client messages, add logic here.
            # Example: await ws_manager.broadcast(f"Client {client_addr} sent: {data}")
    except WebSocketDisconnect as e:
        logger.info(
            f"WebSocket disconnected by client: {client_addr} (Code: {e.code}, Reason: {e.reason or 'N/A'})"
        )
    except Exception as e:
        # Log unexpected errors during the WebSocket lifecycle
        logger.error(f"WebSocket error for {client_addr}: {e}", exc_info=True)
    finally:
        # Ensure disconnection is handled regardless of how the loop exits
        await ws_manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed and cleaned up for: {client_addr}")
