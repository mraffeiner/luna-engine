from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    BackgroundTasks,
)
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import os
from dotenv import load_dotenv
import asyncio
import threading
from twitchio.ext import commands
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import json
import pickle
import uuid

# Google API Imports
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TWITCH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_NICK = os.getenv("TWITCH_NICK")
TWITCH_CHANNELS_STR = os.getenv("TWITCH_CHANNELS")
TWITCH_CHANNELS = [
    channel.strip().lower()
    for channel in (TWITCH_CHANNELS_STR.split(",") if TWITCH_CHANNELS_STR else [])
    if channel.strip()
]

# YouTube / Google API Config
GOOGLE_CLIENT_SECRETS_FILE = os.getenv(
    "GOOGLE_CLIENT_SECRETS_FILE", "/app/youtube_secret.json"
)
GOOGLE_CREDENTIALS_STORE_DIR = os.getenv(
    "GOOGLE_CREDENTIALS_STORE_DIR", "/app/credentials"
)
GOOGLE_TOKEN_FILE = os.path.join(GOOGLE_CREDENTIALS_STORE_DIR, "youtube_token.pickle")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
]
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8005/oauth2callback"
)

# --- Status Tracking ---
# More detailed status tracking per platform
PlatformStatus = Dict[
    str, str
]  # e.g., {"twitch": "disconnected", "youtube": "auth_required"}
current_status: PlatformStatus = {"twitch": "disconnected", "youtube": "disconnected"}
status_lock = threading.Lock()  # To protect status updates from different threads


def update_status(platform: str, status: str):
    with status_lock:
        current_status[platform] = status
    logger.info(f"Status update: {platform} -> {status}")
    # Optionally broadcast status updates via WebSocket if needed later


# --- WebSocket Connection Manager ---
# ... (ConnectionManager class remains the same) ...
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected: {websocket.client}. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected: {websocket.client}. Total connections: {len(self.active_connections)}"
            )

    async def broadcast(self, message: Dict[str, Any]):
        message_json = json.dumps(message)
        disconnected_connections = []
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(
                    f"Failed to send message to {connection.client}: {e}. Marking for disconnect."
                )
                if connection not in disconnected_connections:
                    disconnected_connections.append(connection)
                    self.disconnect(connection)


manager = ConnectionManager()

# --- Background Task Management ---
twitch_bot_instance: Optional[commands.Bot] = None
twitch_thread: Optional[threading.Thread] = None
twitch_loop: Optional[asyncio.AbstractEventLoop] = None
youtube_thread: Optional[threading.Thread] = None
stop_youtube_listener = threading.Event()
main_event_loop: Optional[asyncio.AbstractEventLoop] = None
google_credentials: Optional[Credentials] = None
youtube_service: Optional[Resource] = None
youtube_live_chat_id: Optional[str] = None
oauth_state_storage: Dict[str, bool] = {}
google_flow: Optional[Flow] = None
pending_auth_url: Optional[str] = None  # Store the auth URL if needed


# --- Google Authentication (Refactored for Web Flow & On-Demand) ---
def initialize_google_flow():
    global google_flow
    if not GOOGLE_CLIENT_SECRETS_FILE or not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
        logger.error(
            f"Google client secrets file not found: {GOOGLE_CLIENT_SECRETS_FILE}"
        )
        update_status("youtube", "error_config")
        return False
    try:
        google_flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=YOUTUBE_SCOPES,
            redirect_uri=OAUTH_REDIRECT_URI,
        )
        logger.info("Google OAuth flow initialized.")
        return True
    except Exception as e:
        logger.exception("Failed to initialize Google OAuth flow.")
        google_flow = None
        update_status("youtube", "error_config")
        return False


def get_google_credentials(initiate_auth_flow: bool = False):
    """
    Gets valid Google credentials. If initiate_auth_flow is True and creds are invalid,
    it generates the auth URL and returns None. Otherwise, returns creds or None.
    """
    global google_credentials, google_flow, pending_auth_url
    creds = None
    os.makedirs(GOOGLE_CREDENTIALS_STORE_DIR, exist_ok=True)

    if os.path.exists(GOOGLE_TOKEN_FILE):
        try:
            with open(GOOGLE_TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
            logger.info("Loaded Google credentials from token file.")
        except Exception as e:
            logger.error(f"Failed to load token file: {e}. Need to re-authenticate.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Google credentials expired, attempting refresh...")
            try:
                creds.refresh(GoogleAuthRequest())
                logger.info("Google credentials refreshed successfully.")
                with open(GOOGLE_TOKEN_FILE, "wb") as token:
                    pickle.dump(creds, token)
                logger.info(
                    f"Saved refreshed Google credentials to {GOOGLE_TOKEN_FILE}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to refresh Google credentials: {e}. Need to re-authenticate."
                )
                if os.path.exists(GOOGLE_TOKEN_FILE):
                    os.remove(GOOGLE_TOKEN_FILE)
                creds = None
                update_status(
                    "youtube", "auth_required"
                )  # Refresh failed, needs full auth
                pending_auth_url = None  # Clear any old URL
        else:
            # No valid/refreshable token
            creds = None
            if initiate_auth_flow:
                if not google_flow:
                    logger.error(
                        "Google OAuth flow not initialized. Cannot start auth process."
                    )
                    update_status("youtube", "error_config")
                    return None

                state = str(uuid.uuid4())
                oauth_state_storage[state] = True
                authorization_url, _ = google_flow.authorization_url(
                    access_type="offline", include_granted_scopes="true", state=state
                )
                pending_auth_url = authorization_url  # Store the URL
                update_status("youtube", "auth_required")
                logger.warning(
                    f"Auth URL generated. Access via API or logs: {authorization_url}"
                )
                logger.warning(
                    "After granting permission, the callback will complete authentication."
                )
                # Return None to signal auth is pending
                return None
            else:
                # If not initiating flow, just report disconnected/auth needed status
                if os.path.exists(
                    GOOGLE_TOKEN_FILE
                ):  # If file exists but wasn't valid/refreshable
                    update_status("youtube", "auth_required")
                else:  # No token file exists at all
                    update_status("youtube", "disconnected")

    # If we reach here with valid creds, update status and store
    if creds and creds.valid:
        google_credentials = creds
        # Don't set status to 'connected' here, wait for listener thread confirmation
        # update_status("youtube", "authenticated") # Or similar intermediate state?
    else:
        google_credentials = None  # Ensure it's None if invalid

    return creds


def build_youtube_service():
    global youtube_service, google_credentials
    if not google_credentials or not google_credentials.valid:
        logger.warning("Cannot build YouTube service: No valid Google credentials.")
        youtube_service = None
        return False
    try:
        youtube_service = build("youtube", "v3", credentials=google_credentials)
        logger.info("YouTube API service built successfully.")
        return True
    except Exception:
        logger.exception("Failed to build YouTube API service.")
        youtube_service = None
        update_status("youtube", "error_api")
        return False


def start_youtube_listener_thread():
    """Starts the YouTube listener thread if conditions are met."""
    global youtube_thread, main_event_loop, youtube_service, youtube_live_chat_id

    if youtube_thread and youtube_thread.is_alive():
        logger.info("YouTube listener thread already running.")
        return

    if not youtube_service:
        logger.warning("Cannot start YouTube listener: Service not built.")
        return

    # Try to find chat ID if not already found
    if not youtube_live_chat_id and YOUTUBE_CHANNEL_ID:
        logger.info("Attempting to find YouTube live chat ID...")
        youtube_live_chat_id = find_active_live_chat_id(
            youtube_service, YOUTUBE_CHANNEL_ID
        )

    if not youtube_live_chat_id:
        logger.warning("Cannot start YouTube listener: Live chat ID not found.")
        return

    if not main_event_loop:
        logger.error("Cannot start YouTube listener: Main event loop not available.")
        return

    logger.info("Starting YouTube listener thread...")
    stop_youtube_listener.clear()  # Ensure stop flag is clear
    youtube_thread = threading.Thread(
        target=run_youtube_listener,
        args=(main_event_loop,),  # Pass main loop
        daemon=True,
        name="YouTubeThread",
    )
    youtube_thread.start()


# --- Twitch Bot ---
class TwitchBot(commands.Bot):
    def __init__(self):
        token = TWITCH_TOKEN
        if token and not token.startswith("oauth:"):
            token = f"oauth:{token}"

        super().__init__(
            token=token,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_NICK,
            prefix="!",
        )

    async def event_ready(self):
        logger.info(f"Twitch Bot logged in as | {self.nick}")
        logger.info(f"Twitch Bot user ID is | {self.user_id}")
        update_status("twitch", "connected")  # Update status on successful login
        if TWITCH_CHANNELS:
            logger.info(f"Joining Twitch channels: {TWITCH_CHANNELS}")
            try:
                await self.join_channels(TWITCH_CHANNELS)
            except Exception as e:
                logger.error(f"Failed to join Twitch channels: {e}")
        else:
            logger.warning(
                "No Twitch channels specified in TWITCH_CHANNELS environment variable."
            )

    async def event_message(self, message):
        if message.echo or not message.content:
            return
        log_message = f"Twitch - {message.channel.name} | {message.author.name}: {message.content}"
        logger.info(log_message)
        broadcast_message = {
            "platform": "twitch",
            "channel": message.channel.name,
            "author": message.author.name,
            "text": message.content,
            "timestamp": (message.timestamp.isoformat() if message.timestamp else None),
        }
        await manager.broadcast(broadcast_message)

    async def event_error(self, error: Exception, data: str = None):
        logger.error(f"Twitch Bot Error: {error}")
        update_status("twitch", "error")  # Update status on error

    async def event_close(self):
        logger.info("Twitch bot connection closed.")
        update_status("twitch", "disconnected")  # Update status on close


def run_twitch_bot_sync():
    global twitch_bot_instance, twitch_loop

    if not (TWITCH_TOKEN and TWITCH_CLIENT_ID):
        logger.warning("Twitch credentials not configured. Cannot start bot.")
        update_status("twitch", "error_config")
        return

    update_status("twitch", "connecting")
    try:
        logger.info("Starting Twitch Bot thread...")
        twitch_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(twitch_loop)
        twitch_bot_instance = TwitchBot()
        twitch_loop.run_until_complete(twitch_bot_instance.start())
    except Exception as e:
        logger.exception(f"Fatal error running Twitch Bot: {e}")
        update_status("twitch", "error")
    finally:
        # Status is set to disconnected via event_close
        if twitch_loop and not twitch_loop.is_closed():
            logger.info("Closing Twitch bot event loop from thread finally block.")
            twitch_loop.close()
        logger.info("Twitch Bot thread finished.")


def stop_twitch_bot():
    global twitch_bot_instance, twitch_loop, twitch_thread
    if twitch_bot_instance and twitch_loop and twitch_loop.is_running():
        logger.info("Attempting to stop Twitch bot via its event loop...")
        future = asyncio.run_coroutine_threadsafe(
            twitch_bot_instance.close(), twitch_loop
        )
        try:
            future.result(timeout=5)
            logger.info("Twitch bot close command sent successfully.")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for Twitch bot close command.")
        except Exception as e:
            logger.error(f"Error sending close command to Twitch bot: {e}")
        # Don't stop the loop here, let event_close handle status and thread cleanup handle loop close
    else:
        logger.info("Twitch bot not running or loop inactive.")
        update_status(
            "twitch", "disconnected"
        )  # Ensure status is correct if already stopped

    # Wait for thread to finish
    if twitch_thread and twitch_thread.is_alive():
        logger.info("Waiting for Twitch thread to finish...")
        twitch_thread.join(timeout=7)  # Slightly longer timeout
        if twitch_thread.is_alive():
            logger.warning("Twitch thread did not finish cleanly.")
        else:
            logger.info("Twitch thread finished.")
    twitch_thread = None  # Clear thread variable


# --- YouTube Chat Listener (Refactored for API & On-Demand Start) ---
def run_youtube_listener(loop: asyncio.AbstractEventLoop):
    global youtube_service, youtube_live_chat_id, stop_youtube_listener

    update_status("youtube", "connecting")  # Mark as connecting

    # Wait for service and chat ID
    while not youtube_service or not youtube_live_chat_id:
        if stop_youtube_listener.is_set():
            logger.info("YouTube listener stopping before initialization complete.")
            update_status("youtube", "disconnected")
            return
        # Check if auth is required based on status potentially set elsewhere
        with status_lock:
            current_yt_status = current_status.get("youtube")
        if current_yt_status == "auth_required":
            logger.warning("YouTube listener waiting: Authentication required.")
        elif current_yt_status == "error_config" or current_yt_status == "error_api":
            logger.error(
                f"YouTube listener stopping due to configuration/API error: {current_yt_status}"
            )
            return  # Stop thread if config/API error occurred
        else:
            logger.info("YouTube listener waiting for service and chat ID...")

        stop_youtube_listener.wait(5)

    logger.info(f"Starting YouTube API polling for chat ID: {youtube_live_chat_id}...")
    update_status("youtube", "connected")  # Mark as connected now polling starts
    next_page_token = None
    polling_interval_ms = 5000

    while not stop_youtube_listener.is_set():
        try:
            request = youtube_service.liveChatMessages().list(
                liveChatId=youtube_live_chat_id,
                part="snippet,authorDetails",
                maxResults=200,
                pageToken=next_page_token,
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                author = item.get("authorDetails", {})
                message_text = snippet.get("displayMessage")
                author_name = author.get("displayName")
                published_at = snippet.get("publishedAt")

                if message_text and author_name and published_at:
                    # logger.info(f"YouTube - {published_at} | {author_name}: {message_text}") # Log only if needed
                    broadcast_message = {
                        "platform": "youtube",
                        "channel": YOUTUBE_CHANNEL_ID,
                        "author": author_name,
                        "text": message_text,
                        "timestamp": published_at,
                    }
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(broadcast_message), loop
                    )

            next_page_token = response.get("nextPageToken")
            polling_interval_ms = response.get(
                "pollingIntervalMillis", polling_interval_ms
            )
            stop_youtube_listener.wait(polling_interval_ms / 1000.0)

        except HttpError as e:
            logger.error(f"YouTube API error: {e.resp.status} {e.content}")
            if e.resp.status == 403:
                logger.error("Quota possibly exceeded. Stopping listener.")
                update_status("youtube", "error_quota")
                break
            elif e.resp.status == 404:
                logger.error("Live chat not found. Stopping listener.")
                update_status("youtube", "error_chat_ended")
                youtube_live_chat_id = None  # Clear ID
                break  # Stop polling
            else:
                update_status("youtube", "error_api")
                stop_youtube_listener.wait(30)
        except Exception as e:
            logger.exception(f"Unexpected error in YouTube Listener loop: {e}")
            update_status("youtube", "error")
            stop_youtube_listener.wait(60)

    logger.info("YouTube Listener thread finished.")
    # Only set to disconnected if not stopped due to specific errors handled above
    with status_lock:
        if current_status.get("youtube") not in [
            "error_quota",
            "error_chat_ended",
            "error_api",
            "error_config",
        ]:
            update_status("youtube", "disconnected")


def stop_youtube_listener_thread():
    global youtube_thread
    logger.info("Signaling YouTube listener to stop...")
    stop_youtube_listener.set()
    if youtube_thread and youtube_thread.is_alive():
        logger.info("Waiting for YouTube thread to finish...")
        youtube_thread.join(timeout=5)
        if youtube_thread.is_alive():
            logger.warning("YouTube thread did not finish cleanly.")
        else:
            logger.info("YouTube thread finished.")
    else:
        # If thread wasn't running, ensure status is disconnected
        update_status("youtube", "disconnected")
    youtube_thread = None  # Clear thread variable


# --- Helper to find Live Chat ID ---
# ... (find_active_live_chat_id remains the same) ...
def find_active_live_chat_id(service, channel_id):
    """Finds the active live chat ID for the given channel."""
    try:
        broadcast_request = service.liveBroadcasts().list(
            part="snippet", broadcastStatus="active", mine=True
        )
        broadcast_response = broadcast_request.execute()
        if not broadcast_response.get("items"):
            logger.info(f"No active live broadcasts found for channel {channel_id}.")
            return None
        active_broadcast = broadcast_response["items"][0]
        live_chat_id = active_broadcast.get("snippet", {}).get("liveChatId")
        if live_chat_id:
            logger.info(f"Found active live chat ID: {live_chat_id}")
            return live_chat_id
        else:
            logger.warning(f"Active broadcast found, but no liveChatId associated.")
            return None
    except HttpError as e:
        logger.error(f"API error finding live broadcast: {e.resp.status} {e.content}")
        update_status("youtube", "error_api")
        return None
    except Exception as e:
        logger.exception("Unexpected error finding live broadcast.")
        update_status("youtube", "error")
        return None


# --- FastAPI Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_event_loop, google_flow
    logger.info("Chat Service starting up...")
    main_event_loop = asyncio.get_running_loop()

    # Override uvicorn access logger format
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] - %(levelname)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
    )
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(handler)
    logger.info("Uvicorn access logger format overridden.")

    # Initialize Google Flow object ONCE on startup
    initialize_google_flow()
    # Attempt to load credentials, but don't initiate auth flow here
    get_google_credentials(initiate_auth_flow=False)
    # Build service if creds are valid now
    build_youtube_service()

    # DO NOT start listener threads automatically anymore
    logger.info("Service ready. Use API endpoints to connect platforms.")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Chat Service shutting down...")
    stop_twitch_bot()  # Use the stop function
    stop_youtube_listener_thread()  # Use the stop function
    logger.info("Shutdown complete.")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Chat Service",
    description="Handles live chat events from Twitch and YouTube, broadcasting via WebSocket.",
    lifespan=lifespan,
)


# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Chat Service is running"}


@app.get("/status", response_model=PlatformStatus)
async def get_status():
    """Returns the current connection status of each platform."""
    with status_lock:
        return current_status.copy()


@app.get("/auth-url")
async def get_auth_url():
    """Returns the Google OAuth URL if authentication is required."""
    global pending_auth_url
    if pending_auth_url:
        url = pending_auth_url
        # Optional: Clear URL after providing it once? Or keep it until auth succeeds?
        # pending_auth_url = None
        return {"auth_url": url}
    else:
        # Check if auth is actually required right now
        get_google_credentials(
            initiate_auth_flow=True
        )  # This will set pending_auth_url if needed
        if pending_auth_url:
            return {"auth_url": pending_auth_url}
        else:
            return {
                "auth_url": None,
                "message": "Authentication not currently required or already completed.",
            }


@app.post("/connect/twitch", response_model=PlatformStatus)
async def connect_twitch(background_tasks: BackgroundTasks):
    """Starts the Twitch bot connection."""
    global twitch_thread
    logger.info("Twitch connect requested...")

    with status_lock:
        if twitch_thread and twitch_thread.is_alive():
            logger.warning("Twitch connect requested but thread already running.")
            return current_status.copy()
        if current_status.get("twitch") == "connecting":
            logger.warning("Twitch connect requested but already connecting.")
            return current_status.copy()

    # Start in background to avoid blocking API response
    background_tasks.add_task(run_twitch_bot_sync)
    # Give a moment for the thread to potentially update status
    await asyncio.sleep(0.1)
    with status_lock:
        return current_status.copy()


@app.post("/disconnect/twitch", response_model=PlatformStatus)
async def disconnect_twitch(background_tasks: BackgroundTasks):
    """Stops the Twitch bot connection."""
    logger.info("Twitch disconnect requested...")

    # Run stop in background to allow graceful shutdown without blocking response
    background_tasks.add_task(stop_twitch_bot)
    await asyncio.sleep(0.1)  # Give a moment for status update
    with status_lock:
        return current_status.copy()


@app.post("/connect/youtube", response_model=PlatformStatus)
async def connect_youtube(background_tasks: BackgroundTasks):
    """Attempts to connect to YouTube chat, may require auth."""
    global google_credentials, youtube_service, youtube_live_chat_id, youtube_thread

    with status_lock:
        if youtube_thread and youtube_thread.is_alive():
            logger.warning("YouTube connect requested but thread already running.")
            return current_status.copy()
        if current_status.get("youtube") == "connecting":
            logger.warning("YouTube connect requested but already connecting.")
            return current_status.copy()

    # 1. Check/Get Credentials - initiate flow if needed
    creds = get_google_credentials(initiate_auth_flow=True)

    if not creds:
        # Auth required or error occurred, status updated by get_google_credentials
        logger.warning(
            "YouTube connection cannot proceed: Credentials not available or auth required."
        )
        with status_lock:
            return (
                current_status.copy()
            )  # Return current status (likely 'auth_required' or 'error_config')

    # 2. Build Service (might already be built by lifespan/callback)
    if not youtube_service:
        if not build_youtube_service():
            logger.error("YouTube connection failed: Could not build service.")
            with status_lock:
                return current_status.copy()  # Status updated by build_youtube_service

    # 3. Find Chat ID (might already be found by lifespan/callback)
    if not youtube_live_chat_id:
        if YOUTUBE_CHANNEL_ID:
            youtube_live_chat_id = find_active_live_chat_id(
                youtube_service, YOUTUBE_CHANNEL_ID
            )
        else:
            logger.warning("YOUTUBE_CHANNEL_ID not set. Cannot find live chat.")
            update_status("youtube", "error_config")  # Config error if ID missing
            with status_lock:
                return current_status.copy()

    if not youtube_live_chat_id:
        logger.warning("YouTube connection failed: Could not find active live chat ID.")
        # Keep status as is, maybe disconnected or error from find_active_live_chat_id
        with status_lock:
            return current_status.copy()

    # 4. Start Listener Thread
    # Use background task to avoid blocking
    background_tasks.add_task(start_youtube_listener_thread)
    await asyncio.sleep(0.1)  # Give thread time to start and update status
    with status_lock:
        return current_status.copy()


@app.post("/disconnect/youtube", response_model=PlatformStatus)
async def disconnect_youtube(background_tasks: BackgroundTasks):
    """Stops the YouTube listener thread."""
    background_tasks.add_task(stop_youtube_listener_thread)
    await asyncio.sleep(0.1)  # Give a moment for status update
    with status_lock:
        return current_status.copy()


@app.get("/oauth2callback")
async def oauth2callback(
    request: Request,
    background_tasks: BackgroundTasks,
    code: str = None,
    state: str = None,
    error: str = None,
):
    """Handles the OAuth 2.0 callback from Google."""
    global google_credentials, youtube_service, youtube_live_chat_id, google_flow, oauth_state_storage, pending_auth_url

    if error:
        logger.error(f"Google OAuth callback error: {error}")
        update_status("youtube", "error_auth")
        return HTMLResponse(
            f"<html><body><h1>Authentication Error</h1><p>{error}</p></body></html>",
            status_code=400,
        )
    if not code:
        logger.error("Google OAuth callback missing 'code'.")
        update_status("youtube", "error_auth")
        return HTMLResponse(
            "<html><body><h1>Authentication Error</h1><p>Missing authorization code.</p></body></html>",
            status_code=400,
        )
    if not state or not oauth_state_storage.pop(state, None):
        logger.error("Google OAuth callback state mismatch or missing state.")
        update_status("youtube", "error_auth")
        return HTMLResponse(
            "<html><body><h1>Authentication Error</h1><p>Invalid state parameter (CSRF protection).</p></body></html>",
            status_code=400,
        )
    if not google_flow:
        logger.error("Google OAuth flow not initialized during callback.")
        update_status("youtube", "error_config")
        return HTMLResponse(
            "<html><body><h1>Internal Server Error</h1><p>OAuth flow not ready.</p></body></html>",
            status_code=500,
        )

    try:
        logger.info("Exchanging authorization code for tokens...")
        google_flow.fetch_token(code=code)
        creds = google_flow.credentials
        google_credentials = creds
        pending_auth_url = None  # Clear pending URL now that auth succeeded
        update_status("youtube", "authenticated")  # Mark as authenticated

        with open(GOOGLE_TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
        logger.info(f"Saved new Google credentials to {GOOGLE_TOKEN_FILE}")

        # Now build service, find chat ID, and trigger listener start in background
        if build_youtube_service():
            if YOUTUBE_CHANNEL_ID:
                youtube_live_chat_id = find_active_live_chat_id(
                    youtube_service, YOUTUBE_CHANNEL_ID
                )
                # Start listener in background after successful auth
                background_tasks.add_task(start_youtube_listener_thread)
            else:
                logger.warning(
                    "YOUTUBE_CHANNEL_ID not set. Cannot find live chat after auth."
                )
                update_status("youtube", "error_config")
        else:
            update_status("youtube", "error_api")  # Failed to build service

        return HTMLResponse(
            "<html><body><h1>Authentication Successful!</h1><p>You can close this window. The chat service is now authenticated. Listener thread starting if live chat found.</p></body></html>"
        )

    except Exception as e:
        logger.exception(f"Error fetching/saving token during OAuth callback: {e}")
        update_status("youtube", "error_auth")
        return HTMLResponse(
            f"<html><body><h1>Authentication Error</h1><p>Failed to process authorization code: {e}</p></body></html>",
            status_code=500,
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # ... (WebSocket endpoint remains the same) ...
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected by client: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error for {websocket.client}: {e}")
    finally:
        manager.disconnect(websocket)


# --- Main Execution ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    logger.info(f"Starting Uvicorn on 0.0.0.0:{port}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )
