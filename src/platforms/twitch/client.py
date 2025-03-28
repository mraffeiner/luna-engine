import asyncio
import logging
from typing import Optional

from twitchio.ext import commands

# Updated relative import paths
from ...config import (
    Platform,
    ConnectionStatus,
    TWITCH_OAUTH_TOKEN,
    TWITCH_CLIENT_ID,
    TWITCH_NICK,
    TWITCH_CHANNELS,
)
from ...services.status_manager import StatusManager
from ...core.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)


# Renamed class to TwitchClient
class TwitchClient(commands.Bot):
    """Represents the Twitch chat client connection and event handling."""

    def __init__(self, status_manager: StatusManager, ws_manager: ConnectionManager):
        self.status_manager = status_manager
        self.ws_manager = ws_manager
        self._token = TWITCH_OAUTH_TOKEN
        # Ensure token has the required 'oauth:' prefix
        if self._token and not self._token.startswith("oauth:"):
            self._token = f"oauth:{self._token}"

        super().__init__(
            token=self._token,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_NICK,
            prefix="!",  # Default prefix, can be changed or ignored if not using commands
            # Consider adding heartbeat options if needed for stability
            # heartbeat=30.0
        )
        logger.info("TwitchClient initialized.")

    async def event_ready(self):
        """Called once the bot goes online."""
        logger.info(f"Twitch Client logged in as | {self.nick} ({self.user_id})")
        self.status_manager.update(Platform.TWITCH, ConnectionStatus.CONNECTED)
        if TWITCH_CHANNELS:
            logger.info(f"Joining Twitch channels: {TWITCH_CHANNELS}")
            try:
                await self.join_channels(TWITCH_CHANNELS)
                logger.info(f"Successfully joined channels: {TWITCH_CHANNELS}")
            except Exception as e:
                # Handle potential errors during join (e.g., invalid channel, auth issues)
                logger.error(f"Failed to join Twitch channels: {e}")
                self.status_manager.update(Platform.TWITCH, ConnectionStatus.ERROR_API)
        else:
            logger.warning("No Twitch channels specified in configuration.")

    async def event_message(self, message):
        """Runs every time a message is sent in chat."""
        if message.echo or not message.content:
            return

        broadcast_message = {
            "platform": Platform.TWITCH.value,
            "channel": message.channel.name,
            "author": message.author.name,
            "text": message.content,
            "timestamp": (message.timestamp.isoformat() if message.timestamp else None),
        }
        await self.ws_manager.broadcast(broadcast_message)

    async def event_error(self, error: Exception, data: Optional[str] = None):
        """Runs when an error occurs."""
        log_message = f"Twitch Client Error: {error}"
        if data:
            log_message += f" | Data: {data}"
        logger.error(log_message, exc_info=True)
        self.status_manager.update(Platform.TWITCH, ConnectionStatus.ERROR)

    async def event_close(self):
        """Runs when the bot connection is closed."""
        logger.info("Twitch client connection closed.")
        self.status_manager.update(Platform.TWITCH, ConnectionStatus.DISCONNECTED)

    async def run(self):
        """
        Connects and runs the Twitch client's internal loop.
        Handles startup checks, connection, and cleanup.
        This method is intended to be run as an asyncio task.
        """
        # Check for necessary configuration before attempting to start
        if not (self._token and TWITCH_CLIENT_ID and TWITCH_NICK):
            logger.warning(
                "Twitch credentials incomplete (Token, Client ID, or Nick missing). Cannot start client."
            )
            self.status_manager.update(Platform.TWITCH, ConnectionStatus.ERROR_CONFIG)
            return  # Exit if config is missing

        self.status_manager.update(Platform.TWITCH, ConnectionStatus.CONNECTING)
        logger.info("Starting Twitch Client task...")

        try:
            # self.start() runs the bot's internal loop until closed or cancelled
            await self.start()
        except asyncio.CancelledError:
            logger.info("Twitch Client task cancelled.")
            # Ensure connection is closed gracefully on cancellation
            if getattr(self, "is_connected", False):
                await self.close()
        except Exception as e:
            # Catch potential exceptions during startup or runtime
            logger.exception(f"Fatal error running Twitch Client task: {e}")
            self.status_manager.update(Platform.TWITCH, ConnectionStatus.ERROR)
        finally:
            # Ensure the status is correctly set after the task finishes
            current_status = self.status_manager.get(Platform.TWITCH)
            if current_status not in [
                ConnectionStatus.DISCONNECTED,  # Already set by event_close
                ConnectionStatus.ERROR,
                ConnectionStatus.ERROR_CONFIG,
            ]:
                logger.warning(
                    f"Twitch client task finished unexpectedly (status: {current_status.value}). Forcing status to disconnected."
                )
                self.status_manager.update(
                    Platform.TWITCH, ConnectionStatus.DISCONNECTED
                )
            logger.info("Twitch Client task finished.")
            # Ensure bot is closed if not already handled by cancellation or event_close
            if getattr(self, "is_connected", False):
                try:
                    await self.close()
                    logger.info("Twitch Client connection closed during final cleanup.")
                except Exception:
                    logger.exception(
                        "Error closing Twitch Client during final cleanup."
                    )
