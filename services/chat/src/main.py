import logging

import uvicorn
from fastapi import FastAPI
from typing import Optional
from fastapi import Request, BackgroundTasks, Depends, Query, status
from fastapi.responses import HTMLResponse

# Import configurations
from .config import (
    API_PORT,
    API_HOST,
    WS_PING_INTERVAL,
    WS_PING_TIMEOUT,
)

# Import core components
from .core.lifespan import lifespan  # Updated lifespan import
from .core import websocket as websocket_router  # Import websocket router

from .services.chat_orchestrator import ChatOrchestrator
from .core.dependencies import get_chat_orchestrator

# Import API routers
from .routers import chat as chat_router

# Import logging setup
from .utils.logging_config import setup_logging

# --- Logging Setup ---
# Configure logging using the centralized setup function
setup_logging()
logger = logging.getLogger(__name__)


# --- FastAPI App Initialization ---
# Initialize FastAPI with the lifespan context manager from core.lifespan
app = FastAPI(
    title="Chat Service",
    description="Handles live chat events from Twitch and YouTube, broadcasting via WebSocket.",
    lifespan=lifespan,  # Use imported lifespan
)

# --- Include Routers ---
# Mount the API routers
app.include_router(chat_router.router)
app.include_router(websocket_router.router)  # Include WebSocket router


# --- OAuth Callback Route (No Prefix) ---
@app.get("/oauth2callback")
async def oauth2callback(
    request: Request,  # Keep for full URL access if needed by auth manager
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """Handles the OAuth 2.0 callback from Google via the orchestrator."""
    logger.info(
        f"API: Received OAuth callback. State: {state}, Code: {'present' if code else 'missing'}, Error: {error}"
    )

    if error:
        logger.error(f"API: Google OAuth callback error: {error}")
        return HTMLResponse(
            f"<html><head><title>Auth Error</title></head><body><h1>Authentication Error</h1><p>An error occurred during Google authentication: {error}. Please check the service logs and try again.</p></body></html>",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not code or not state:
        error_detail = "Missing 'code'" if not code else "Missing 'state'"
        logger.error(f"API: Google OAuth callback error: {error_detail}.")
        return HTMLResponse(
            f"<html><head><title>Auth Error</title></head><body><h1>Authentication Error</h1><p>{error_detail} parameter from Google. Please try the authentication process again.</p></body></html>",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Process the callback via the orchestrator
    success = orchestrator.process_oauth_callback(code, state)

    if success:
        logger.info(
            "API: OAuth callback processed successfully. Triggering YouTube poller start if needed."
        )
        await orchestrator.connect_youtube()
        return HTMLResponse(
            "<html><head><title>Auth Success</title></head><body><h1>Authentication Successful!</h1><p>You have successfully authenticated with Google. You can close this window now. The YouTube chat poller will attempt to connect if required.</p></body></html>"
        )
    else:
        # Error status should have been set by the auth manager via the orchestrator
        logger.error("API: Failed to process OAuth callback.")
        return HTMLResponse(
            "<html><head><title>Auth Error</title></head><body><h1>Authentication Error</h1><p>Failed to process the authorization code received from Google. Please check the service logs for more details and try again.</p></body></html>",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# --- Main Execution ---
if __name__ == "__main__":
    # Logging is configured by setup_logging() before this point
    logger.info(f"Starting Uvicorn server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        # Point uvicorn to the 'app' instance in 'chat-service.src.main'
        "chat-service.src.main:app",
        host=API_HOST,
        port=API_PORT,
        log_level=logging.getLogger().getEffectiveLevel(),  # Use root logger level
        ws_ping_interval=WS_PING_INTERVAL,
        ws_ping_timeout=WS_PING_TIMEOUT,
        reload=False,  # IMPORTANT: Keep reload=False for production/docker
        # Use reload_dirs only for local development:
        # reload=True,
        # reload_dirs=["chat-service/src"]
    )
