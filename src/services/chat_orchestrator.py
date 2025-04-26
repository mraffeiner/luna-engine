import asyncio
import logging
from typing import Dict, Optional, List, Any

from fastapi import BackgroundTasks

from .status_manager import StatusManager
from ..core.websocket_manager import ConnectionManager
from ..platforms.youtube.auth import GoogleAuthManager
from ..platforms.youtube.poller import YouTubePoller

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
        youtube_poller: YouTubePoller,
    ):
        self.status_manager = status_manager
        self.ws_manager = ws_manager
        self.google_auth_manager = google_auth_manager
        self.youtube_poller = youtube_poller
        logger.info("ChatOrchestrator initialized.")

    def get_all_status(self) -> Dict[Platform, ConnectionStatus]:
        """Returns the current connection status of all platforms."""
        return self.status_manager.get_all()

    def get_youtube_auth_url(self) -> Optional[str]:
        """Generates the Google OAuth URL if needed."""
        return self.google_auth_manager.generate_auth_url()

    def process_oauth_callback(self, code: str, state: str) -> bool:
        """Processes the OAuth callback, fetches token, and updates status."""
        return self.google_auth_manager.process_oauth_callback(code, state)

    async def connect_youtube(self):
        """Starts the YouTube poller initialization."""
        logger.info("Orchestrator: YouTube connect requested.")

        if self.status_manager.get(Platform.YOUTUBE) == ConnectionStatus.AUTH_REQUIRED:
            logger.warning(
                "Orchestrator: YouTube connection cannot proceed: Authentication required."
            )
            return

        logger.info(
            "Orchestrator: Checking YouTube credentials before starting poller..."
        )
        creds = self.google_auth_manager.get_credentials(initiate_auth_flow=True)

        if not creds:
            logger.warning(
                "Orchestrator: YouTube authentication required. Poller not started."
            )
            return

        logger.info(
            "Orchestrator: YouTube credentials valid. Proceeding to initialize poller."
        )
        self.status_manager.update(Platform.YOUTUBE, ConnectionStatus.CONNECTING)

        logger.info("Orchestrator: Initializing YouTube poller.")
        self.youtube_poller.start()

    async def disconnect_youtube(self):
        """Stops the YouTube poller."""
        logger.info("Orchestrator: YouTube disconnect requested.")
        self.youtube_poller.stop()
        logger.info("Orchestrator: YouTube poller stopped.")

    async def connect_twitch(self, app_state: dict):
        """Creates a new TwitchClient instance and starts its connection task."""
        logger.info("Orchestrator: Twitch connect requested.")

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
        from ..platforms.twitch.client import TwitchClient

        new_twitch_client = TwitchClient(self.status_manager, self.ws_manager)

        task = asyncio.create_task(
            new_twitch_client.run(), name=f"TwitchClientTask-{id(new_twitch_client)}"
        )

        app_state.platform_tasks[Platform.TWITCH] = task
        app_state.platform_instances[Platform.TWITCH] = new_twitch_client

        # Small delay to allow task to potentially start and update status
        await asyncio.sleep(0.05)

    async def disconnect_twitch(
        self, app_state: dict, background_tasks: BackgroundTasks
    ):
        """Stops the running Twitch client connection task."""
        logger.info("Orchestrator: Twitch disconnect requested.")

        current_task = app_state.platform_tasks.get(Platform.TWITCH)

        if current_task and not current_task.done():
            logger.info(
                f"Orchestrator: Cancelling Twitch client task {current_task.get_name()}..."
            )
            current_task.cancel()
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)

            # Add a background task to wait for cancellation with a timeout
            async def _wait_for_cancel(task):
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                    logger.info("Orchestrator: Twitch task cancellation confirmed.")
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

            background_tasks.add_task(_wait_for_cancel, current_task)

        else:
            logger.info("Orchestrator: Twitch task not running or already finished.")
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)
            if self.status_manager.get(Platform.TWITCH) not in [
                ConnectionStatus.DISCONNECTED,
                ConnectionStatus.ERROR_CONFIG,
                ConnectionStatus.ERROR,
                ConnectionStatus.ERROR_API,
                ConnectionStatus.ERROR_AUTH,
            ]:
                self.status_manager.update(
                    Platform.TWITCH, ConnectionStatus.DISCONNECTED
                )

    async def disconnect_all(self, app_state: dict):
        """Disconnects all active platform connections gracefully."""
        logger.info("Orchestrator: Disconnecting all platforms...")
        tasks_to_wait_for = []

        twitch_task = app_state.platform_tasks.get(Platform.TWITCH)
        if twitch_task and not twitch_task.done():
            logger.info(
                f"Orchestrator: Cancelling Twitch task {twitch_task.get_name()} during shutdown..."
            )
            twitch_task.cancel()
            tasks_to_wait_for.append(twitch_task)

        logger.info("Orchestrator: Stopping YouTube poller during shutdown...")
        self.youtube_poller.stop()

        if tasks_to_wait_for:
            logger.info(
                f"Orchestrator: Waiting for {len(tasks_to_wait_for)} tasks to cancel..."
            )
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
            app_state.platform_tasks.pop(Platform.TWITCH, None)
            app_state.platform_instances.pop(Platform.TWITCH, None)

        logger.info("Orchestrator: All platforms disconnected.")

    async def poll_youtube_messages(self):
        """
        Performs a single poll of YouTube Live Chat messages via the poller.
        Returns a list of new messages.
        """
        logger.info("Orchestrator: Received request to poll YouTube chat.")
        await self.youtube_poller.poll_messages()
        return {"status": "OK"}
