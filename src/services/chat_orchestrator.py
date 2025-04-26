import asyncio
import logging
from typing import Dict, Optional

from fastapi import BackgroundTasks

# Import managers, platform clients, config, and dependencies
from .status_manager import StatusManager
from ..core.websocket_manager import ConnectionManager
from ..platforms.youtube.auth import GoogleAuthManager
from ..platforms.youtube.listener import YouTubeListener

# TwitchClient is now imported directly where needed, not injected into orchestrator init
# from ..platforms.twitch.client import TwitchClient
from ..config import (
    Platform,
    ConnectionStatus,
)

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """Orchestrates connections and interactions with chat platforms."""

    def __init__(
        self,
        status_manager: StatusManager,
        ws_manager: ConnectionManager,
        google_auth_manager: GoogleAuthManager,
        youtube_listener: YouTubeListener,
        # twitch_client: TwitchClient, # Removed from init
    ):
        self.status_manager = status_manager
        self.ws_manager = ws_manager
        self.google_auth_manager = google_auth_manager
        self.youtube_listener = youtube_listener
        # self.twitch_client = twitch_client # Removed instance variable
        # Store task/thread references and client instances in app.state
        logger.info("ChatOrchestrator initialized.")

    # --- Status ---
    def get_all_status(self) -> Dict[Platform, ConnectionStatus]:
        """Returns the current connection status of all platforms."""
        return self.status_manager.get_all()

    # --- YouTube Methods ---
    def get_youtube_auth_url(self) -> Optional[str]:
        """Generates the Google OAuth URL if needed."""
        # Auth manager updates status internally if auth is required
        return self.google_auth_manager.generate_auth_url()

    def process_oauth_callback(self, code: str, state: str) -> bool:
        """Processes the OAuth callback, fetches token, and updates status."""
        # Auth manager handles token fetching, saving, and status updates
        return self.google_auth_manager.process_oauth_callback(code, state)

    async def connect_youtube(self, background_tasks: BackgroundTasks):
        """Starts the YouTube listener thread if conditions are met."""
        logger.info("Orchestrator: YouTube connect requested.")
        current_status = self.status_manager.get(Platform.YOUTUBE)

        if self.youtube_listener.thread and self.youtube_listener.thread.is_alive():
            logger.warning(
                "Orchestrator: YouTube connect requested but listener is already running."
            )
            return
        if current_status == ConnectionStatus.CONNECTING:
            logger.warning(
                "Orchestrator: YouTube connect requested but connection is already in progress."
            )
            return

        # Check credentials status via auth_manager or status_manager
        if self.status_manager.get(Platform.YOUTUBE) == ConnectionStatus.AUTH_REQUIRED:
            logger.warning(
                "Orchestrator: YouTube connection cannot proceed: Authentication required."
            )
            # Status should already be AUTH_REQUIRED
            return  # Don't proceed

        # --- Check Credentials Before Starting Listener ---
        logger.info(
            "Orchestrator: Checking YouTube credentials before starting listener..."
        )
        # Attempt to get credentials, initiating auth flow if necessary
        creds = self.google_auth_manager.get_credentials(initiate_auth_flow=True)

        if not creds:
            # get_credentials returned None, meaning auth is required.
            # The status is already set to AUTH_REQUIRED by get_credentials.
            logger.warning(
                "Orchestrator: YouTube authentication required. Listener not started."
            )
            # The frontend should react to the AUTH_REQUIRED status.
            return  # Do not proceed to start the listener

        # --- Credentials Valid - Proceed to Start Listener ---
        logger.info(
            "Orchestrator: YouTube credentials valid. Proceeding to start listener."
        )
        # Update status to CONNECTING immediately and broadcast
        self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTING)

        logger.info("Orchestrator: Starting YouTube listener via background task.")
        # The listener's start method handles thread creation and further status updates
        current_loop = asyncio.get_running_loop()
        background_tasks.add_task(self.youtube_listener.start, current_loop)

    async def disconnect_youtube(self, background_tasks: BackgroundTasks):
        """Stops the YouTube listener thread."""
        logger.info("Orchestrator: YouTube disconnect requested.")
        if not (
            self.youtube_listener.thread and self.youtube_listener.thread.is_alive()
        ):
            logger.warning(
                "Orchestrator: YouTube disconnect requested but listener is not running."
            )
            # Ensure status is correct if not running
            if self.status_manager.get(Platform.YOUTUBE) not in [
                ConnectionStatus.DISCONNECTED,
                ConnectionStatus.AUTH_REQUIRED,
                ConnectionStatus.ERROR_CONFIG,
            ]:
                self.status_manager.update(
                    Platform.YOUTUBE, ConnectionStatus.DISCONNECTED
                )
            return

        logger.info("Orchestrator: Stopping YouTube listener via background task.")
        # The listener's stop method handles thread signaling and status updates
        background_tasks.add_task(self.youtube_listener.stop)
        await asyncio.sleep(0.1)  # Allow status update propagation

    # --- Twitch Methods ---
    async def connect_twitch(
        self, app_state: dict
    ):  # Pass app_state to manage task and instance refs
        """Creates a new TwitchClient instance and starts its connection task."""
        logger.info("Orchestrator: Twitch connect requested.")

        # Access state dictionaries directly (initialized in lifespan.py)
        current_task = app_state.platform_tasks.get(Platform.TWITCH)
        current_status = self.status_manager.get(Platform.TWITCH)

        if current_task and not current_task.done():
            logger.warning(
                "Orchestrator: Twitch connect requested but task is already running."
            )
            return
        if current_status == ConnectionStatus.CONNECTING:
            logger.warning(
                "Orchestrator: Twitch connect requested but connection is already in progress."
            )
            return

        logger.info("Orchestrator: Creating new TwitchClient instance and task.")
        # Import here to avoid circular dependency issues if TwitchClient needs orchestrator
        from ..platforms.twitch.client import TwitchClient

        # Create a NEW instance
        new_twitch_client = TwitchClient(self.status_manager, self.ws_manager)

        # Create the task using the new instance's run method
        task = asyncio.create_task(
            new_twitch_client.run(), name=f"TwitchClientTask-{id(new_twitch_client)}"
        )

        # Store references in app.state using attribute access
        app_state.platform_tasks[Platform.TWITCH] = task
        app_state.platform_instances[Platform.TWITCH] = new_twitch_client

        # Status will be updated by the client task itself
        await asyncio.sleep(0.05)  # Allow task to start and potentially update status

    async def disconnect_twitch(
        self, app_state: dict, background_tasks: BackgroundTasks
    ):
        """Stops the running Twitch client connection task."""
        logger.info("Orchestrator: Twitch disconnect requested.")

        # Access state dictionaries directly (initialized in lifespan.py)
        current_task = app_state.platform_tasks.get(Platform.TWITCH)

        if current_task and not current_task.done():
            logger.info(
                f"Orchestrator: Cancelling Twitch client task {current_task.get_name()}..."
            )
            current_task.cancel()
            # Clear references from app.state using attribute access
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)

            # Optional: Wait for cancellation in background for logging
            async def wait_for_cancel(task):
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.CancelledError:
                    logger.info("Orchestrator: Twitch task cancellation confirmed.")
                except asyncio.TimeoutError:
                    logger.warning(
                        "Orchestrator: Timeout waiting for Twitch task cancellation."
                    )
                except Exception:
                    logger.exception(
                        "Orchestrator: Error waiting for Twitch task cancellation."
                    )

            background_tasks.add_task(wait_for_cancel, current_task)
            await asyncio.sleep(0.05)  # Allow cancellation to start and status updates
        else:
            logger.info("Orchestrator: Twitch task not running or already finished.")
            # Clear any potentially stale references using attribute access
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)
            # Ensure status is correct
            if self.status_manager.get(Platform.TWITCH) not in [
                ConnectionStatus.DISCONNECTED,
                ConnectionStatus.ERROR_CONFIG,  # Keep error status if it was set
                ConnectionStatus.ERROR,
                ConnectionStatus.ERROR_API,
                ConnectionStatus.ERROR_AUTH,
            ]:
                self.status_manager.update(
                    Platform.TWITCH, ConnectionStatus.DISCONNECTED
                )

    # --- Shutdown Method ---
    async def disconnect_all(self, app_state: dict, timeout: float = 10.0):
        """Disconnects all active platform connections gracefully."""
        logger.info("Orchestrator: Disconnecting all platforms...")
        # Access state dictionaries directly (initialized in lifespan.py)
        tasks_to_wait_for = []

        # Stop Twitch Task
        twitch_task = app_state.platform_tasks.get(Platform.TWITCH)
        if twitch_task and not twitch_task.done():
            logger.info(
                f"Orchestrator: Cancelling Twitch task {twitch_task.get_name()} during shutdown..."
            )
            twitch_task.cancel()
            tasks_to_wait_for.append(twitch_task)
            # References will be cleared after waiting

        # Stop YouTube Thread (using its own stop method)
        if self.youtube_listener.thread and self.youtube_listener.thread.is_alive():
            logger.info("Orchestrator: Stopping YouTube listener during shutdown...")
            # youtube_listener.stop() is blocking, run in executor? Or assume it's fast enough?
            # For simplicity here, call directly. Consider executor for long-running stops.
            try:
                self.youtube_listener.stop(
                    timeout=timeout * 0.7
                )  # Allocate portion of timeout
            except Exception:
                logger.exception(
                    "Orchestrator: Error stopping YouTube listener during shutdown."
                )

        # Wait for asyncio tasks to finish cancellation
        if tasks_to_wait_for:
            logger.info(
                f"Orchestrator: Waiting for {len(tasks_to_wait_for)} tasks to cancel..."
            )
            # Use asyncio.gather with return_exceptions=True
            results = await asyncio.gather(*tasks_to_wait_for, return_exceptions=True)
            for i, result in enumerate(results):
                task_name = (
                    tasks_to_wait_for[i].get_name()
                    if hasattr(tasks_to_wait_for[i], "get_name")
                    else f"Task-{i}"
                )
                if isinstance(result, asyncio.CancelledError):
                    logger.info(
                        f"Orchestrator: Task {task_name} cancellation confirmed during shutdown."
                    )
                elif isinstance(result, Exception):
                    logger.warning(
                        f"Orchestrator: Task {task_name} raised exception during shutdown cancellation: {result}"
                    )
                else:
                    logger.info(
                        f"Orchestrator: Task {task_name} finished during shutdown wait."
                    )
            logger.info("Orchestrator: Finished waiting for task cancellations.")
            # Clear instance references after tasks are handled using attribute access
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)

        logger.info("Orchestrator: All platforms disconnected.")

    # --- YouTube Trigger Method ---
    def trigger_youtube_poll(self):
        """Triggers the YouTube listener to perform a poll."""
        logger.info("Orchestrator: Received request to trigger YouTube poll.")
        self.youtube_listener.trigger_poll()
