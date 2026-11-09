import logging
from datetime import datetime

from datetime import datetime
import logging
from typing import Dict, List, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Request,
    Depends,
)

from ..config import Platform, ConnectionStatus
from ..services.chat_orchestrator import ChatOrchestrator
from ..core.dependencies import get_chat_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Chat"],
)


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


@router.get("/")
async def read_root():
    """Basic endpoint to check if the service is running."""
    return {"message": "Chat Service is running"}


@router.get("/status", response_model=Dict[Platform, ConnectionStatus])
async def get_status(orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)):
    """Returns the current connection status of each platform."""
    return orchestrator.get_all_status()


@router.get("/auth-url")
async def get_auth_url(orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator)):
    """Generates and returns the Google OAuth URL."""
    auth_url = orchestrator.get_youtube_auth_url()
    if auth_url:
        return {"auth_url": auth_url}
    else:
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
        return {"auth_url": None, "message": message}


@router.post("/connect/twitch", response_model=Dict[Platform, ConnectionStatus])
async def connect_twitch(
    request: Request,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Starts the Twitch connection task."""
    logger.info("API: Twitch connect requested.")
    await orchestrator.connect_twitch(request.app.state)
    return orchestrator.get_all_status()


@router.post("/disconnect/twitch", response_model=Dict[Platform, ConnectionStatus])
async def disconnect_twitch(
    request: Request,
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Stops the Twitch connection task."""
    logger.info("API: Twitch disconnect requested.")
    await orchestrator.disconnect_twitch(request.app.state, background_tasks)
    return orchestrator.get_all_status()


@router.post("/connect/youtube", response_model=Dict[Platform, ConnectionStatus])
async def connect_youtube(
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Starts the YouTube poller initialization."""
    logger.info("API: YouTube connect requested.")
    await orchestrator.connect_youtube()
    return orchestrator.get_all_status()


@router.post("/disconnect/youtube", response_model=Dict[Platform, ConnectionStatus])
async def disconnect_youtube(
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Stops the YouTube poller."""
    logger.info("API: YouTube disconnect requested.")
    await orchestrator.disconnect_youtube()
    return orchestrator.get_all_status()


@router.get("/youtube/poll")
async def poll_youtube_messages(
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """
    Polls YouTube Live Chat messages.
    Returns a list of new messages.
    """
    logger.info("API: YouTube poll requested.")
    await orchestrator.poll_youtube_messages()
    return {"status": "OK"}
