import asyncio
import logging
import threading
from typing import Optional

from googleapiclient.errors import HttpError

# Updated relative import paths
from ...config import Platform, ConnectionStatus, YOUTUBE_CHANNEL_ID, GOOGLE_TOKEN_FILE
from ...services.status_manager import StatusManager
from ...core.websocket_manager import ConnectionManager
from .auth import GoogleAuthManager  # Use the renamed auth module
import os  # For checking/removing token file on auth error

logger = logging.getLogger(__name__)


class YouTubeListener:
    """Handles connecting to and polling YouTube Live Chat via the API."""

    def __init__(
        self,
        auth_manager: GoogleAuthManager,
        status_manager: StatusManager,
        ws_manager: ConnectionManager,
    ):
        self.auth_manager = auth_manager
        self.status_manager = status_manager
        self.ws_manager = ws_manager
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.live_chat_id: Optional[str] = None
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None  # Set during start

    def _find_active_live_chat_id(self) -> Optional[str]:
        """Finds the active live chat ID for the configured channel using the YouTube API."""
        if not self.auth_manager.youtube_service:
            logger.warning("Cannot find chat ID: YouTube service not available.")
            # Status should reflect why service isn't available (e.g., AUTH_REQUIRED, ERROR_CONFIG)
            return None
        if not YOUTUBE_CHANNEL_ID:
            logger.warning("Cannot find chat ID: YOUTUBE_CHANNEL_ID not set.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG)
            return None

        logger.info(
            f"Attempting to find YouTube live chat ID for channel {YOUTUBE_CHANNEL_ID}..."
        )
        try:
            # Use 'mine=True' if the authenticated user IS the channel owner.
            # Adjust if searching for broadcasts on other channels (requires different permissions/logic).
            # Request 'status' part to check lifeCycleStatus locally.
            broadcast_request = self.auth_manager.youtube_service.liveBroadcasts().list(
                part="snippet,status",
                mine=True,  # Cannot use broadcastStatus with mine=True
            )
            broadcast_response = broadcast_request.execute()

            active_broadcast = None
            for item in broadcast_response.get("items", []):
                # Check the lifeCycleStatus to find the truly 'live' broadcast
                if item.get("status", {}).get("lifeCycleStatus") == "live":
                    active_broadcast = item
                    break  # Found the active one

            if not active_broadcast:
                logger.info(
                    f"No active ('live' lifeCycleStatus) broadcasts found for channel {YOUTUBE_CHANNEL_ID}."
                )
                # If no stream is active, update status to indicate this.
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.ERROR_NO_LIVE_CHAT
                )
                return None

            # Found the active broadcast, now get the chat ID
            chat_id = active_broadcast.get("snippet", {}).get("liveChatId")
            if chat_id:
                logger.info(f"Found active live chat ID: {chat_id}")
                return chat_id
            else:
                logger.warning("Active broadcast found, but no liveChatId associated.")
                # This might indicate a configuration issue or API change.
                self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_API)
                return None
        except HttpError as e:
            logger.error(
                f"API error finding live broadcast: {e.resp.status} {e.content.decode('utf-8', 'ignore')}"
            )
            if e.resp.status == 403:
                # Could be quota, permissions, or disabled API
                content_str = e.content.decode("utf-8", "ignore").lower()
                if "quota" in content_str:
                    self.status_manager.update(
                        Platform.YOUTUBE, ConnectionStatus.ERROR_QUOTA
                    )
                else:  # Assume permission issue otherwise
                    self.status_manager.update(
                        Platform.YOUTUBE, ConnectionStatus.ERROR_AUTH
                    )
            else:
                self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_API)
            return None
        except Exception:
            logger.exception("Unexpected error finding live broadcast.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR)
            return None

    def _run_polling(self):
        """The main polling loop executed within the listener thread."""
        if not self.main_loop:
            logger.error(
                "Cannot run YouTube listener polling: Main event loop not set."
            )
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR)
            return

        # --- Wait for prerequisites ---
        while not self.stop_event.is_set():
            logger.warning("Entering polling loop.")
            # 1. Check Credentials & Service
            if not self.auth_manager.youtube_service:
                # Attempt to get credentials without initiating flow (it might have been fixed)
                creds = self.auth_manager.get_credentials(initiate_auth_flow=False)
                if not creds:  # Auth still required or error occurred
                    current_yt_status = self.status_manager.get(Platform.YOUTUBE)
                    if current_yt_status == ConnectionStatus.AUTH_REQUIRED:
                        logger.warning(
                            "YouTube listener waiting: Authentication required."
                        )
                    elif current_yt_status in [
                        ConnectionStatus.ERROR_CONFIG,
                        ConnectionStatus.ERROR_API,
                        ConnectionStatus.ERROR_AUTH,
                    ]:
                        logger.error(
                            f"YouTube listener stopping due to error: {current_yt_status.value}"
                        )
                        return  # Stop thread if unrecoverable error
                    else:  # Status is likely CONNECTING or DISCONNECTED (if no token file existed)
                        # Don't force DISCONNECTED here. Let the auth flow handle AUTH_REQUIRED.
                        logger.info(
                            "YouTube listener waiting: No valid credentials found yet."
                        )
                        # Status remains as it is (e.g., CONNECTING)
                    if self.stop_event.wait(10):
                        return  # Wait and check stop event
                    continue  # Re-check credentials
                else:  # Creds became valid, try building service
                    if not self.auth_manager._build_service():
                        logger.error(
                            "YouTube listener stopping: Failed to build service after getting creds."
                        )
                        # Status already set by _build_service
                        return  # Stop thread

            # 2. Find Chat ID (only if service is available)
            if not self.live_chat_id:
                logger.warning("No live chat ID found.")
                self.live_chat_id = self._find_active_live_chat_id()
                if not self.live_chat_id:
                    # Status (DISCONNECTED or ERROR_*) already set by _find_active_live_chat_id
                    logger.warning(
                        "YouTube listener could not find active chat ID. Will retry later if connect is called again."
                    )
                    # Don't stop the thread here, let it exit naturally.
                    # It will only restart polling if connect_youtube is called again.
                    return  # Exit the run loop

            # If we got here, service and chat ID are ready for polling
            break  # Exit prerequisite loop

        if self.stop_event.is_set():
            logger.info("YouTube listener stopping during initialization.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.DISCONNECTED)
            return

        # --- Start Polling ---
        logger.info(f"Starting YouTube API polling for chat ID: {self.live_chat_id}...")
        self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTED)
        next_page_token = None
        polling_interval_ms = 5000  # Default, will be updated by API response

        while not self.stop_event.is_set():
            logger.warning("Started polling.")
            try:
                request = self.auth_manager.youtube_service.liveChatMessages().list(
                    liveChatId=self.live_chat_id,
                    part="snippet,authorDetails",
                    maxResults=200,  # Max allowed by API
                    pageToken=next_page_token,
                )
                response = request.execute()

                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    author = item.get("authorDetails", {})
                    message_text = snippet.get("displayMessage")
                    author_name = author.get("displayName")
                    published_at = snippet.get("publishedAt")  # ISO 8601 format

                    if message_text and author_name and published_at:
                        broadcast_message = {
                            "platform": Platform.YOUTUBE.value,
                            "channel": YOUTUBE_CHANNEL_ID or "unknown",
                            "author": author_name,
                            "text": message_text,
                            "timestamp": published_at,
                        }
                        # Schedule broadcast on the main event loop
                        asyncio.run_coroutine_threadsafe(
                            self.ws_manager.broadcast(broadcast_message), self.main_loop
                        )

                next_page_token = response.get("nextPageToken")
                # Use the polling interval suggested by the API
                polling_interval_ms = response.get(
                    "pollingIntervalMillis", polling_interval_ms
                )
                # Wait for the specified interval, checking stop_event periodically
                wait_time_secs = polling_interval_ms / 1000.0
                logger.warning(f"Wait time: {wait_time_secs}s.")

                # Safeguard
                if wait_time_secs < 1:
                    wait_time_secs = 1

                if self.stop_event.wait(wait_time_secs):
                    break  # Stop requested during wait

            except HttpError as e:
                content_str = e.content.decode("utf-8", "ignore").lower()
                logger.error(f"YouTube API error: {e.resp.status} {content_str}")
                error_status = ConnectionStatus.ERROR_API
                should_break = False
                wait_secs = 30  # Default wait time on error

                if e.resp.status == 401 or e.resp.status == 403:
                    # More specific handling for auth/permission/quota errors
                    if (
                        "invalid_grant" in content_str
                        or "token has been expired" in content_str
                        or "token was revoked" in content_str
                    ):
                        logger.error(
                            "Authentication error (token invalid/expired/revoked). Re-authentication required."
                        )
                        error_status = ConnectionStatus.AUTH_REQUIRED
                        self.auth_manager.credentials = None  # Clear invalid creds
                        if os.path.exists(GOOGLE_TOKEN_FILE):
                            try:
                                os.remove(GOOGLE_TOKEN_FILE)
                                logger.info(
                                    f"Removed stale token file: {GOOGLE_TOKEN_FILE}"
                                )
                            except OSError:
                                logger.error(
                                    f"Failed to remove stale token file: {GOOGLE_TOKEN_FILE}"
                                )
                        should_break = True  # Stop polling, requires user action
                    elif "quota" in content_str:
                        logger.error("Quota possibly exceeded.")
                        error_status = ConnectionStatus.ERROR_QUOTA
                        should_break = True  # Stop polling if quota hit
                    elif "disabled" in content_str:  # e.g., API not enabled
                        logger.error("YouTube API access is disabled.")
                        error_status = (
                            ConnectionStatus.ERROR_API
                        )  # Or a more specific error?
                        should_break = True
                    else:  # Other 403, likely permissions
                        logger.error("Permission denied error.")
                        error_status = ConnectionStatus.ERROR_AUTH
                        should_break = True
                elif e.resp.status == 404:
                    # Could be chat not found or broadcast ended
                    if "livechatnotfound" in content_str:
                        logger.error(
                            "Live chat not found (possibly ended or incorrect ID)."
                        )
                        error_status = ConnectionStatus.ERROR_CHAT_ENDED
                        self.live_chat_id = None  # Clear ID
                        should_break = True  # Stop polling
                    else:  # Other 404
                        error_status = ConnectionStatus.ERROR_API
                        wait_secs = 60  # Wait longer for potentially transient 404s

                self.status_manager.update(Platform.YOUTUBE, error_status)
                if should_break:
                    break  # Exit polling loop
                else:
                    if self.stop_event.wait(wait_secs):
                        break  # Wait and check stop event

            except Exception:
                logger.exception("Unexpected error in YouTube Listener polling loop.")
                self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR)
                if self.stop_event.wait(60):
                    break  # Longer wait on unexpected errors

        logger.info("YouTube Listener polling loop finished.")
        # Set status to disconnected unless it was stopped due to a specific error state
        # that requires user intervention or indicates the chat ended.
        final_status = self.status_manager.get(Platform.YOUTUBE)
        if final_status not in [
            ConnectionStatus.AUTH_REQUIRED,
            ConnectionStatus.ERROR_QUOTA,
            ConnectionStatus.ERROR_CHAT_ENDED,
            ConnectionStatus.ERROR_CONFIG,
            ConnectionStatus.ERROR_AUTH,
        ]:
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.DISCONNECTED)

    def start(self, main_loop: asyncio.AbstractEventLoop):
        """
        Starts the listener thread if not already running.
        Requires the main asyncio event loop to be passed for scheduling callbacks.
        """
        if self.thread and self.thread.is_alive():
            logger.info("YouTube listener thread already running.")
            return False  # Indicate already running

        if not main_loop:
            logger.error("Cannot start YouTube listener: No event loop provided.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR)
            return False

        self.main_loop = main_loop  # Store the provided event loop

        # Reset state before starting
        self.stop_event.clear()
        self.live_chat_id = None  # Force re-finding chat ID on each start

        logger.info("Starting YouTube listener thread...")
        self.status_manager.update(
            Platform.YOUTUBE, ConnectionStatus.CONNECTING
        )  # Set status early
        self.thread = threading.Thread(
            target=self._run_polling,
            daemon=True,  # Daemon threads exit automatically when main program exits
            name="YouTubeThread",
        )
        self.thread.start()
        return True  # Indicate thread started

    def stop(self, timeout: float = 7.0):
        """Signals the listener thread to stop and waits for it to join."""
        if not self.thread or not self.thread.is_alive():
            logger.info("YouTube listener thread not running or already stopped.")
            # Ensure status reflects disconnected state if no error prevents it
            current_status = self.status_manager.get(Platform.YOUTUBE)
            if current_status not in [
                ConnectionStatus.ERROR_CONFIG,
                ConnectionStatus.AUTH_REQUIRED,
                ConnectionStatus.ERROR_AUTH,
                ConnectionStatus.ERROR_QUOTA,
            ]:
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.DISCONNECTED
                )
            self.thread = None  # Ensure thread variable is cleared
            return

        logger.info("Signaling YouTube listener thread to stop...")
        self.stop_event.set()
        self.thread.join(timeout=timeout)

        if self.thread.is_alive():
            logger.warning(
                f"YouTube listener thread did not finish within {timeout}s timeout."
            )
            # Consider more forceful shutdown if necessary, but usually not recommended
        else:
            logger.info("YouTube listener thread finished joining.")

        self.thread = None  # Clear thread variable after joining attempt
        # Final status is set within _run_polling or updated here if thread wasn't running
