import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

# Import managers from new locations
from .websocket_manager import ConnectionManager
from ..services.status_manager import StatusManager

# Import platform modules from new locations
from ..platforms.youtube.auth import GoogleAuthManager
from ..platforms.youtube.listener import YouTubeListener

# from ..platforms.twitch.client import TwitchClient # Removed singleton import

# Import the orchestrator
from ..services.chat_orchestrator import ChatOrchestrator

# Import config for state keys
from ..config import (
    STATE_WS_MANAGER,
    STATE_CHAT_ORCHESTRATOR,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles application startup and shutdown events."""
    logger.info("Chat Service starting up...")

    # --- Initialize Core Components ---
    # These instances will be shared via app.state and accessed via dependencies
    main_loop = asyncio.get_running_loop()
    ws_manager = ConnectionManager()
    status_manager = StatusManager(
        ws_manager=ws_manager, main_loop=main_loop
    )  # Pass ws_manager and loop
    google_auth_manager = GoogleAuthManager(status_manager)
    youtube_listener = YouTubeListener(google_auth_manager, status_manager, ws_manager)
    # twitch_client = TwitchClient(status_manager, ws_manager) # Removed singleton creation

    # Initialize the orchestrator, passing necessary components
    chat_orchestrator = ChatOrchestrator(
        status_manager=status_manager,
        ws_manager=ws_manager,
        google_auth_manager=google_auth_manager,
        youtube_listener=youtube_listener,
        # twitch_client=twitch_client, # Removed twitch_client argument
    )

    # Store instances in app.state using the defined constant keys for dependency injection
    setattr(app.state, STATE_WS_MANAGER, ws_manager)
    setattr(app.state, STATE_CHAT_ORCHESTRATOR, chat_orchestrator)

    # Store other managers directly for now, in case they are accessed differently
    # (Though ideally, access should be standardized via dependencies or the orchestrator)
    app.state.status_manager = status_manager
    app.state.google_auth_manager = google_auth_manager
    app.state.youtube_listener = youtube_listener
    # app.state.twitch_client = twitch_client # Removed storing singleton

    # Store the asyncio task and instance reference dicts in state for orchestrator use
    app.state.platform_tasks = {}
    app.state.platform_instances = {}  # Added for consistency

    logger.info("Core components initialized. Ready for connections.")

    yield  # Application runs here

    # --- Shutdown Sequence ---
    logger.info("Chat Service shutting down...")

    # Retrieve orchestrator and ws_manager using the keys for consistency during shutdown
    orchestrator: ChatOrchestrator = getattr(app.state, STATE_CHAT_ORCHESTRATOR)
    ws_manager_instance: ConnectionManager = getattr(app.state, STATE_WS_MANAGER)

    # 1. Stop Platform Connections via Orchestrator
    if orchestrator:
        logger.info("Initiating platform disconnection via orchestrator...")
        await orchestrator.disconnect_all(app_state=app.state, timeout=10.0)
    else:
        logger.warning("Chat orchestrator not found in state during shutdown.")

    # 2. Close WebSocket connections
    if ws_manager_instance:
        logger.info("Closing active WebSocket connections...")
        # Use a list copy to avoid modification issues during iteration
        connections_to_close = list(
            ws_manager_instance.active_connections
        )  # Create a copy
        closed_count = 0
        for ws in connections_to_close:
            try:
                # Use code 1001 for "Going Away" (server shutdown)
                await ws.close(code=1001, reason="Server shutting down")
                closed_count += 1
            except Exception:
                logger.warning(f"Error closing a WebSocket connection.", exc_info=False)
        logger.info(f"Attempted to close {closed_count} WebSocket connections.")
    else:
        logger.warning("WebSocket manager not found in state during shutdown.")

    logger.info("Shutdown complete.")
