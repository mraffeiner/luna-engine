import asyncio
import threading
import logging
from typing import Dict

# Updated relative import paths
from ..config import Platform, ConnectionStatus
from ..core.websocket_manager import ConnectionManager


logger = logging.getLogger(__name__)


class StatusManager:
    """Manages the connection status for different chat platforms."""

    def __init__(
        self, ws_manager: ConnectionManager, main_loop: asyncio.AbstractEventLoop
    ):
        self._status: Dict[Platform, ConnectionStatus] = {
            Platform.TWITCH: ConnectionStatus.DISCONNECTED,
            Platform.YOUTUBE: ConnectionStatus.DISCONNECTED,
        }
        # Use threading.Lock as status might be updated/read from different threads (YouTube poller)
        self._lock = threading.Lock()
        # Store ws_manager and main_loop for broadcasting updates
        self.ws_manager: ConnectionManager = ws_manager
        self.main_loop: asyncio.AbstractEventLoop = main_loop

    def update(self, platform: Platform, status: ConnectionStatus):
        """Updates the status for a given platform if it has changed and broadcasts the update."""
        with self._lock:
            if self._status.get(platform) != status:
                self._status[platform] = status
                logger.info(f"Status update: {platform.value} -> {status.value}")
                # Broadcast the status change via WebSocket manager
                if self.ws_manager and self.main_loop:
                    message = {
                        "type": "status_update",
                        "platform": platform.value,
                        "status": status.value,
                    }
                    # Schedule the async broadcast call on the main event loop
                    asyncio.run_coroutine_threadsafe(
                        self.ws_manager.broadcast(message), self.main_loop
                    )

    def get(self, platform: Platform) -> ConnectionStatus:
        """Gets the current status for a given platform."""
        with self._lock:
            return self._status.get(platform, ConnectionStatus.DISCONNECTED)

    def get_all(self) -> Dict[Platform, ConnectionStatus]:
        """Gets a copy of the current status for all platforms."""
        with self._lock:
            return self._status.copy()
