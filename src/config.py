import os
import logging
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --- Enums ---
class Platform(str, Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"  # YouTube specific intermediate state
    AUTH_REQUIRED = "auth_required"  # YouTube specific
    ERROR = "error"
    ERROR_CONFIG = "error_config"
    ERROR_API = "error_api"
    ERROR_AUTH = "error_auth"
    ERROR_QUOTA = "error_quota"  # YouTube specific
    ERROR_CHAT_ENDED = "error_chat_ended"  # YouTube specific


# --- Twitch Configuration ---
TWITCH_OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_NICK = os.getenv("TWITCH_NICK")
TWITCH_CHANNELS_STR = os.getenv("TWITCH_CHANNELS")
TWITCH_CHANNELS = [
    channel.strip().lower()
    for channel in (TWITCH_CHANNELS_STR.split(",") if TWITCH_CHANNELS_STR else [])
    if channel.strip()
]

# --- YouTube / Google API Configuration ---
GOOGLE_CLIENT_SECRETS_FILE = os.getenv(
    "GOOGLE_CLIENT_SECRETS_FILE",
    "/app/youtube_secret.json",  # Assuming running in Docker
)
GOOGLE_CREDENTIALS_STORE_DIR = os.getenv(
    "GOOGLE_CREDENTIALS_STORE_DIR", "/app/credentials"  # Assuming running in Docker
)
GOOGLE_TOKEN_FILE = os.path.join(GOOGLE_CREDENTIALS_STORE_DIR, "youtube_token.pickle")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
]
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8005/oauth2callback"  # Adjust if needed
)
OAUTH_STATE_STORAGE_KEY = "oauth_states"  # Key for storing state in app.state

# --- Application Settings ---
API_PORT = int(os.getenv("PORT", 8005))
API_HOST = os.getenv("HOST", "0.0.0.0")
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", 20))
WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", 20))


# --- State Keys for Dependency Injection ---
STATE_WS_MANAGER = "websocket_manager"
STATE_CHAT_ORCHESTRATOR = "chat_orchestrator"

# --- Validation (Optional but recommended) ---
if not TWITCH_OAUTH_TOKEN or not TWITCH_CLIENT_ID or not TWITCH_NICK:
    logging.getLogger(__name__).warning(
        "Twitch configuration incomplete (Token, Client ID, or Nick missing). Twitch functionality may be limited."
    )

if not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
    logging.getLogger(__name__).warning(
        f"Google client secrets file not found at {GOOGLE_CLIENT_SECRETS_FILE}. YouTube functionality requires authentication setup."
    )

if not YOUTUBE_CHANNEL_ID:
    logging.getLogger(__name__).warning(
        "YOUTUBE_CHANNEL_ID not set. YouTube chat functionality requires a channel ID."
    )
