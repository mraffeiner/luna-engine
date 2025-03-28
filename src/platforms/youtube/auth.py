import os
import pickle
import uuid
import logging
from typing import Optional, Dict

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import Resource, build

# Updated relative import paths
from ...config import (
    Platform,
    ConnectionStatus,
    GOOGLE_CLIENT_SECRETS_FILE,
    GOOGLE_CREDENTIALS_STORE_DIR,
    GOOGLE_TOKEN_FILE,
    YOUTUBE_SCOPES,
    OAUTH_REDIRECT_URI,
    # OAUTH_STATE_STORAGE_KEY, # No longer needed from config
)
from ...services.status_manager import StatusManager  # Updated import path

logger = logging.getLogger(__name__)


class GoogleAuthManager:
    """Handles Google OAuth 2.0 flow, credential management, and YouTube service building."""

    def __init__(self, status_manager: StatusManager):  # Removed app_state
        # self.app_state = app_state # Removed app_state dependency
        self.status_manager = status_manager
        self.flow: Optional[Flow] = None
        self.credentials: Optional[Credentials] = None
        self.oauth_states: Dict[str, bool] = {}  # Internal storage for OAuth states
        self.youtube_service: Optional[Resource] = None
        self.pending_auth_url: Optional[str] = None

        if not GOOGLE_CLIENT_SECRETS_FILE or not os.path.exists(
            GOOGLE_CLIENT_SECRETS_FILE
        ):
            logger.error(
                f"Google client secrets file not found: {GOOGLE_CLIENT_SECRETS_FILE}"
            )
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG)
            return  # Cannot proceed without secrets file

        try:
            self.flow = Flow.from_client_secrets_file(
                GOOGLE_CLIENT_SECRETS_FILE,
                scopes=YOUTUBE_SCOPES,
                redirect_uri=OAUTH_REDIRECT_URI,
            )
            logger.info("Google OAuth flow initialized.")
            # Attempt to load credentials and build service on startup
            self._load_credentials()
            if self.credentials and self.credentials.valid:
                self._build_service()
            elif (
                not self.credentials
            ):  # Only update status if loading failed completely
                # Status is set by _load_credentials (AUTH_REQUIRED or DISCONNECTED)
                pass

        except Exception:
            logger.exception("Failed to initialize Google OAuth flow.")
            self.flow = None
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG)

    def _save_credentials(self):
        """Saves the current credentials to the token file."""
        if self.credentials:
            try:
                os.makedirs(GOOGLE_CREDENTIALS_STORE_DIR, exist_ok=True)
                with open(GOOGLE_TOKEN_FILE, "wb") as token:
                    pickle.dump(self.credentials, token)
                logger.info(f"Saved Google credentials to {GOOGLE_TOKEN_FILE}")
            except Exception:
                logger.exception(
                    f"Failed to save Google credentials to {GOOGLE_TOKEN_FILE}"
                )
                # Should we update status here? Maybe not, as it's an internal error.

    def _load_credentials(self):
        """Loads credentials from file, refreshes if expired, updates status if needed."""
        creds = None
        if os.path.exists(GOOGLE_TOKEN_FILE):
            try:
                with open(GOOGLE_TOKEN_FILE, "rb") as token:
                    creds = pickle.load(token)
                logger.info("Loaded Google credentials from token file.")
            except Exception as e:
                logger.error(f"Failed to load token file: {e}. Need re-auth.")
                creds = None  # Ensure creds is None if loading failed

        if creds and creds.valid:
            self.credentials = creds
            # Don't set status to connected/authenticated yet, wait for listener attempt
            return  # Valid creds loaded

        if creds and creds.expired and creds.refresh_token:
            logger.info("Google credentials expired, attempting refresh...")
            try:
                creds.refresh(GoogleAuthRequest())
                logger.info("Google credentials refreshed successfully.")
                self.credentials = creds
                self._save_credentials()
                # Don't set status yet
                return  # Refreshed creds loaded
            except Exception as e:
                logger.error(
                    f"Failed to refresh Google credentials: {e}. Need re-auth."
                )
                # Remove the invalid token file
                if os.path.exists(GOOGLE_TOKEN_FILE):
                    try:
                        os.remove(GOOGLE_TOKEN_FILE)
                        logger.info(f"Removed stale token file: {GOOGLE_TOKEN_FILE}")
                    except OSError:
                        logger.error(
                            f"Failed to remove stale token file: {GOOGLE_TOKEN_FILE}"
                        )
                self.credentials = None
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.AUTH_REQUIRED
                )
                self.pending_auth_url = None  # Clear any old URL
                return  # Refresh failed

        # If we reach here: No token file, loading failed, or token invalid/unrefreshable
        self.credentials = None
        if os.path.exists(
            GOOGLE_TOKEN_FILE
        ):  # File existed but wasn't valid/refreshable
            logger.warning(
                "Token file exists but credentials are invalid or unrefreshable. Setting status to AUTH_REQUIRED."
            )
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.AUTH_REQUIRED)

    def _build_service(self) -> bool:
        """Builds the YouTube API service using current credentials."""
        if not self.credentials or not self.credentials.valid:
            logger.warning("Cannot build YouTube service: No valid Google credentials.")
            self.youtube_service = None
            # Don't update status here, let the caller handle it based on context
            return False
        try:
            self.youtube_service = build("youtube", "v3", credentials=self.credentials)
            logger.info("YouTube API service built successfully.")
            return True
        except Exception:
            logger.exception("Failed to build YouTube API service.")
            self.youtube_service = None
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_API)
            return False

    def get_credentials(
        self, initiate_auth_flow: bool = False
    ) -> Optional[Credentials]:
        """
        Gets valid credentials. If initiate_auth_flow is True and creds are invalid/missing,
        it generates the auth URL and returns None. Otherwise, returns creds or None.
        """
        # Check current state first
        if self.credentials and self.credentials.valid:
            return self.credentials

        # Attempt to load/refresh again in case state changed since init
        self._load_credentials()
        if self.credentials and self.credentials.valid:
            return self.credentials

        # If still no valid creds, and we should initiate the auth flow
        if initiate_auth_flow:
            if not self.flow:
                logger.error(
                    "Google OAuth flow not initialized. Cannot start auth process."
                )
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG
                )
                return None  # Config error prevents auth flow

            # Generate state for CSRF protection
            state = str(uuid.uuid4())
            # Store state internally
            self.oauth_states[state] = True  # Store state value

            try:
                authorization_url, _ = self.flow.authorization_url(
                    access_type="offline", include_granted_scopes="true", state=state
                )
                self.pending_auth_url = authorization_url
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.AUTH_REQUIRED
                )
                logger.warning(
                    f"Auth URL generated. Access via API or logs: {authorization_url}"
                )
                return None  # Signal that authentication flow needs to be initiated
            except Exception as e:
                logger.exception(f"Failed to generate authorization URL: {e}")
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.ERROR_AUTH
                )
                return None

        # If not initiating flow, status is already set by _load_credentials
        # (either AUTH_REQUIRED or DISCONNECTED)
        return None

    def generate_auth_url(self) -> Optional[str]:
        """Generates and returns the auth URL if needed, otherwise None."""
        # This ensures the status is updated to AUTH_REQUIRED if needed
        self.get_credentials(initiate_auth_flow=True)
        return self.pending_auth_url

    def process_oauth_callback(self, code: str, state: str) -> bool:
        """
        Processes the OAuth callback from Google.
        Validates state, fetches token, saves credentials, and builds the service.
        Returns True on success, False on failure.
        """
        # 1. Validate state parameter
        if not state or not self.oauth_states.pop(
            state, None
        ):  # Use internal dict and pop
            logger.error("Google OAuth callback state mismatch or missing/used state.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_AUTH)
            # Consider adding a cleanup mechanism for old states in self.oauth_states if needed
            return False

        # 2. Check if flow is initialized
        if not self.flow:
            logger.error("Google OAuth flow not initialized during callback.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG)
            return False

        # 3. Exchange code for token
        try:
            logger.info("Exchanging authorization code for tokens...")
            self.flow.fetch_token(code=code)
            self.credentials = self.flow.credentials
            self.pending_auth_url = None  # Clear pending URL on successful auth
            self.status_manager.update(
                Platform.YOUTUBE, ConnectionStatus.AUTHENTICATED
            )  # Intermediate status
            logger.info("Token fetch successful.")

            # 4. Save credentials
            self._save_credentials()

            # 5. Build YouTube service
            if self._build_service():
                logger.info("YouTube service built successfully after OAuth callback.")
                return True
            else:
                # _build_service already updated status to ERROR_API
                logger.error("Failed to build YouTube service after successful OAuth.")
                return False  # Service build failed

        except Exception as e:
            logger.exception(f"Error fetching/saving token during OAuth callback: {e}")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_AUTH)
            self.credentials = None  # Ensure credentials are None on error
            return False
