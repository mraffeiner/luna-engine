import logging
from datetime import datetime

from typing import Dict

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Query,
    Request,  # Keep Request for app.state access temporarily
    Depends,
)

# Import config enums
from ..config import Platform, ConnectionStatus

# Import the orchestrator and the dependency getter
from ..services.chat_orchestrator import ChatOrchestrator
from ..core.dependencies import get_chat_orchestrator

logger = logging.getLogger(__name__)

# Create an APIRouter instance
router = APIRouter(
    tags=["Chat"],  # Add tags for OpenAPI documentation grouping
)


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


# --- API Endpoints ---
# Endpoints now use Depends to get the ChatOrchestrator


@router.get("/")
async def read_root():
    """Basic endpoint to check if the service is running."""
    # No dependency needed for this simple check
    return {"message": "Chat Service is running"}


@router.get("/status", response_model=Dict[Platform, ConnectionStatus])
async def get_status(orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)):
    """Returns the current connection status of each platform via the orchestrator."""
    return orchestrator.get_all_status()


@router.get("/auth-url")
async def get_auth_url(orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)):
    """Generates and returns the Google OAuth URL via the orchestrator."""
    auth_url = orchestrator.get_youtube_auth_url()
    if auth_url:
        return {"auth_url": auth_url}
    else:
        # Orchestrator/AuthManager should have set the status correctly
        yt_status = orchestrator.get_all_status().get(Platform.YOUTUBE)
        message = "Authentication not currently required or possible."
        if (
            yt_status == ConnectionStatus.AUTHENTICATED
            or yt_status == ConnectionStatus.CONNECTED
        ):
            message = "Already authenticated and/or connected."
        elif yt_status == ConnectionStatus.ERROR_CONFIG:
            message = "Cannot generate Auth URL due to configuration error."
        elif yt_status == ConnectionStatus.ERROR_AUTH:
            message = "Cannot generate Auth URL due to a previous authentication error."
        # Add other specific error cases if needed
        return {"auth_url": None, "message": message}


@router.post("/connect/twitch", response_model=Dict[Platform, ConnectionStatus])
async def connect_twitch(
    request: Request,  # Still need request for app.state
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Starts the Twitch connection task via the orchestrator."""
    logger.info("API: Twitch connect requested.")
    # Pass app.state for task management (temporary)
    await orchestrator.connect_twitch(request.app.state)
    return orchestrator.get_all_status()


@router.post("/disconnect/twitch", response_model=Dict[Platform, ConnectionStatus])
async def disconnect_twitch(
    request: Request,  # Still need request for app.state
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Stops the Twitch connection task via the orchestrator."""
    logger.info("API: Twitch disconnect requested.")
    # Pass app.state for task management (temporary)
    await orchestrator.disconnect_twitch(request.app.state, background_tasks)
    return orchestrator.get_all_status()


@router.post("/connect/youtube", response_model=Dict[Platform, ConnectionStatus])
async def connect_youtube(
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Starts the YouTube listener thread via the orchestrator."""
    logger.info("API: YouTube connect requested.")
    await orchestrator.connect_youtube(background_tasks)
    return orchestrator.get_all_status()


@router.post("/disconnect/youtube", response_model=Dict[Platform, ConnectionStatus])
async def disconnect_youtube(
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Stops the YouTube listener thread via the orchestrator."""
    logger.info("API: YouTube disconnect requested.")
    await orchestrator.disconnect_youtube(background_tasks)
    return orchestrator.get_all_status()


@router.post("/trigger-youtube-poll")
async def trigger_youtube_poll(
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Triggers the YouTube listener to perform a poll."""
    logger.info("API: YouTube poll trigger requested.")
    orchestrator.trigger_youtube_poll()
    return {"message": "YouTube poll triggered"}
