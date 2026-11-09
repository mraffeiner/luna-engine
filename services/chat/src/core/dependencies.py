import logging
from fastapi import Request, HTTPException, status

# Import types for managers and orchestrator
from .websocket_manager import ConnectionManager

from ..services.chat_orchestrator import ChatOrchestrator

# Import config for state keys (Consider moving keys to a dedicated constants file later)
from ..config import (
    STATE_WS_MANAGER,
    STATE_CHAT_ORCHESTRATOR,
)

logger = logging.getLogger(__name__)

# --- Dependency Provider Functions ---


def _get_from_state(request: Request, key: str, expected_type: type):
    """Helper to safely retrieve an item from app.state."""
    instance = getattr(request.app.state, key, None)
    if instance is None:
        logger.error(
            f"'{key}' not found in application state. Lifespan setup might have failed."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal configuration error: {key} not initialized.",
        )
    if not isinstance(instance, expected_type):
        logger.error(
            f"'{key}' in application state has unexpected type: {type(instance).__name__}. Expected: {expected_type.__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal configuration error: Invalid type for {key}.",
        )
    return instance


def get_ws_manager(request: Request) -> ConnectionManager:
    """Dependency to get the ConnectionManager instance."""
    return _get_from_state(request, STATE_WS_MANAGER, ConnectionManager)


def get_chat_orchestrator(request: Request) -> ChatOrchestrator:
    """Dependency to get the ChatOrchestrator instance."""
    return _get_from_state(request, STATE_CHAT_ORCHESTRATOR, ChatOrchestrator)
