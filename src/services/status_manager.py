import threading
import logging
from typing import Dict
from ..config import Platform, ConnectionStatus  # Updated import path

logger = logging.getLogger(__name__)


class StatusManager:
    """Manages the connection status for different chat platforms."""

    def __init__(self):
        self._status: Dict[Platform, ConnectionStatus] = {
            Platform.TWITCH: ConnectionStatus.DISCONNECTED,
            Platform.YOUTUBE: ConnectionStatus.DISCONNECTED,
        }
        # Use threading.Lock as status might be updated/read from different threads (YouTube listener)
        self._lock = threading.Lock()

    def update(self, platform: Platform, status: ConnectionStatus):
        """Updates the status for a given platform if it has changed."""
        with self._lock:
            if self._status.get(platform) != status:
                self._status[platform] = status
                logger.info(f"Status update: {platform.value} -> {status.value}")
                # TODO: Consider adding a callback mechanism or event system
                #       to notify other components (like WebSocket manager) of status changes.

    def get(self, platform: Platform) -> ConnectionStatus:
        """Gets the current status for a given platform."""
        with self._lock:
            return self._status.get(platform, ConnectionStatus.DISCONNECTED)

    def get_all(self) -> Dict[Platform, ConnectionStatus]:
        """Gets a copy of the current status for all platforms."""
        with self._lock:
            return self._status.copy()
