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
        logger.debug(
            f"Attempting to call self.start() on TwitchClient instance {id(self)}"
        )  # Add logging
        was_cancelled = False  # Flag to track cancellation
        try:
            # self.start() runs the bot's internal loop until closed or cancelled
            await self.start()
        except asyncio.CancelledError:
            was_cancelled = True  # Set flag on cancellation
            logger.info(
                "Twitch Client task cancelled. Relying on twitchio internal cleanup."
            )
            # Removed explicit self.close() call on cancellation.
            # twitchio might handle this internally when the task is cancelled.
            # The event_close handler should still set the status correctly.
            pass  # Explicitly do nothing here now
        except Exception as e:
            # Catch potential exceptions during startup or runtime
            logger.exception(f"Fatal error running Twitch Client task: {e}")
            self.status_manager.update(Platform.TWITCH, ConnectionStatus.ERROR)
        finally:
            # Ensure the status is correctly set after the task finishes.
            # event_close might have already set it, but this is a safeguard.
            final_status_to_set = None
            current_status = self.status_manager.get(Platform.TWITCH)

            # Check if the status needs to be forced to DISCONNECTED
            if current_status not in [
                ConnectionStatus.DISCONNECTED,  # Already correctly set
                ConnectionStatus.ERROR,  # Preserve specific error states
                ConnectionStatus.ERROR_CONFIG,
                ConnectionStatus.ERROR_API,
                ConnectionStatus.ERROR_AUTH,
            ]:
                final_status_to_set = ConnectionStatus.DISCONNECTED
                # Log differently based on whether cancellation was expected
                if not was_cancelled:
                    logger.warning(
                        f"Twitch client task finished unexpectedly (status: {current_status.value}). Forcing status to disconnected."
                    )
                else:
                    logger.info(
                        f"Twitch client task finished (cancelled). Ensuring status is disconnected (was {current_status.value})."
                    )
            # Apply the final status if needed
            if final_status_to_set:
                self.status_manager.update(Platform.TWITCH, final_status_to_set)

            logger.info("Twitch Client task finished.")
            # Removed redundant close() call from finally block.
            # The CancelledError handler or event_close should handle closing.
