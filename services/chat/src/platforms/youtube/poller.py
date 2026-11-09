import asyncio
import logging
import time
from typing import Optional, List, Dict, Any

from googleapiclient.errors import HttpError

from ...config import Platform, ConnectionStatus, YOUTUBE_CHANNEL_ID, GOOGLE_TOKEN_FILE
from ...services.status_manager import StatusManager
from ...core.websocket_manager import ConnectionManager
from .auth import GoogleAuthManager
import os

logger = logging.getLogger(__name__)


class YouTubePoller:
    """Handles connecting to and polling YouTube Live Chat."""

    def __init__(
        self,
        auth_manager: GoogleAuthManager,
        status_manager: StatusManager,
        ws_manager: ConnectionManager,
    ):
        self.auth_manager = auth_manager
        self.status_manager = status_manager
        self.ws_manager = ws_manager
        self.live_chat_id: Optional[str] = None
        self._next_page_token: Optional[str] = None
        self._polling_interval_millis: int = 1000
        self._last_poll_time: float = 0.0

    def _find_active_live_chat_id(self) -> Optional[str]:
        """Finds the active live chat ID for the configured channel."""
        if not self.auth_manager.youtube_service:
            logger.warning("Cannot find chat ID: YouTube service not available.")
            return None
        if not YOUTUBE_CHANNEL_ID:
            logger.warning("Cannot find chat ID: YOUTUBE_CHANNEL_ID not set.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_CONFIG)
            return None

        logger.info(
            f"Attempting to find YouTube live chat ID for channel {YOUTUBE_CHANNEL_ID}..."
        )
        try:
            broadcast_request = self.auth_manager.youtube_service.liveBroadcasts().list(
                part="snippet,status",
                mine=True,
            )
            broadcast_response = broadcast_request.execute()

            active_broadcast = None
            for item in broadcast_response.get("items", []):
                if item.get("status", {}).get("lifeCycleStatus") == "live":
                    active_broadcast = item
                    break

            if not active_broadcast:
                logger.info(
                    f"No active ('live' lifeCycleStatus) broadcasts found for channel {YOUTUBE_CHANNEL_ID}."
                )
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.ERROR_NO_LIVE_CHAT
                )
                return None

            chat_id = active_broadcast.get("snippet", {}).get("liveChatId")
            if chat_id:
                logger.info(f"Found active live chat ID: {chat_id}")
                return chat_id
            else:
                logger.warning("Active broadcast found, but no liveChatId associated.")
                self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR_API)
                return None
        except HttpError as e:
            logger.error(
                f"API error finding live broadcast: {e.resp.status} {e.content.decode('utf-8', 'ignore')}"
            )
            if e.resp.status == 403:
                content_str = e.content.decode("utf-8", "ignore").lower()
                if "quota" in content_str:
                    self.status_manager.update(
                        Platform.YOUTUBE, ConnectionStatus.ERROR_QUOTA
                    )
                else:
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

    async def poll_messages(self):
        """
        Performs a single poll of YouTube Live Chat messages.
        Respects the minimum polling interval returned by the API.
        Returns a list of new messages.
        """
        current_time = time.time()
        elapsed_since_last_poll = current_time - self._last_poll_time
        min_wait_secs = self._polling_interval_millis / 1000.0

        if elapsed_since_last_poll < min_wait_secs:
            wait_time = min_wait_secs - elapsed_since_last_poll
            logger.info(f"Polling too soon. Waiting for {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)
            current_time = time.time()  # Update time after waiting

        self._last_poll_time = current_time  # Update last poll time before API call

        if not self.auth_manager.youtube_service:
            logger.warning("Cannot poll: YouTube service not available.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.AUTH_REQUIRED)
            return

        if not self.live_chat_id:
            self.live_chat_id = self._find_active_live_chat_id()
            if not self.live_chat_id:
                logger.warning("Cannot poll: No active live chat ID found.")
                return

        logger.info(f"Performing YouTube API poll for chat ID: {self.live_chat_id}...")
        try:
            request = self.auth_manager.youtube_service.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part="snippet,authorDetails",
                maxResults=200,
                pageToken=self._next_page_token,
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                author = item.get("authorDetails", {})
                message_text = snippet.get("displayMessage")
                author_name = author.get("displayName")
                published_at = snippet.get("publishedAt")

                if message_text and author_name and published_at:
                    broadcast_message = {
                        "platform": Platform.YOUTUBE.value,
                        "channel": YOUTUBE_CHANNEL_ID or "unknown",
                        "author": author_name,
                        "text": message_text,
                        "timestamp": published_at,
                    }
                    await self.ws_manager.broadcast(broadcast_message)

            self._next_page_token = response.get("nextPageToken")
            self._polling_interval_millis = response.get("pollingIntervalMillis", 1000)

            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTED)
            return

        except HttpError as e:
            content_str = e.content.decode("utf-8", "ignore").lower()
            logger.error(
                f"YouTube API error during poll: {e.resp.status} {content_str}"
            )
            error_status = ConnectionStatus.ERROR_API

            if e.resp.status == 401 or e.resp.status == 403:
                if (
                    "invalid_grant" in content_str
                    or "token has been expired" in content_str
                    or "token was revoked" in content_str
                ):
                    logger.error(
                        "Authentication error (token invalid/expired/revoked). Re-authentication required."
                    )
                    error_status = ConnectionStatus.AUTH_REQUIRED
                    self.auth_manager.credentials = None
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
                elif "quota" in content_str:
                    logger.error("Quota possibly exceeded.")
                    error_status = ConnectionStatus.ERROR_QUOTA
                elif "disabled" in content_str:
                    logger.error("YouTube API access is disabled.")
                    error_status = ConnectionStatus.ERROR_API
                else:
                    error_status = ConnectionStatus.ERROR_AUTH
            elif e.resp.status == 404:
                if "livechatnotfound" in content_str:
                    logger.error(
                        "Live chat not found (possibly ended or incorrect ID)."
                    )
                    error_status = ConnectionStatus.ERROR_CHAT_ENDED
                    self.live_chat_id = None
                else:
                    error_status = ConnectionStatus.ERROR_API

            self.status_manager.update(Platform.YOUTUBE, error_status)
            raise e

        except Exception:
            logger.exception("Unexpected error during YouTube poll.")
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.ERROR)
            raise e

    def start(self):
        """Initializes the YouTube poller."""
        logger.info("Initializing YouTube poller...")
        self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTING)
        self.live_chat_id = self._find_active_live_chat_id()
        if self.live_chat_id:
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTED)
            logger.info("YouTube poller initialized and connected.")
        else:
            logger.warning(
                "YouTube poller could not initialize: No active chat found or auth failed."
            )

    def stop(self):
        """Stops the YouTube poller and resets its state."""
        logger.info("Stopping YouTube poller.")
        self.live_chat_id = None
        self._next_page_token = None
        self._polling_interval_millis = 1000
        self._last_poll_time = 0.0
        current_status = self.status_manager.get(Platform.YOUTUBE)
        if current_status not in [
            ConnectionStatus.ERROR_CONFIG,
            ConnectionStatus.AUTH_REQUIRED,
            ConnectionStatus.ERROR_AUTH,
            ConnectionStatus.ERROR_QUOTA,
            ConnectionStatus.ERROR_CHAT_ENDED,
            ConnectionStatus.ERROR_NO_LIVE_CHAT,
        ]:
            self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.DISCONNECTED)
