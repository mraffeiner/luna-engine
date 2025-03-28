import os
import logging
import sys

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_uvicorn_logger():
    """Overrides the default uvicorn access logger format."""
    # Ensure uvicorn is available or handle gracefully
    try:
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        # Remove existing handlers to prevent duplicate logs
        for handler in uvicorn_access_logger.handlers[:]:
            uvicorn_access_logger.removeHandler(handler)
        # Add our custom formatted handler
        handler = logging.StreamHandler(sys.stdout)  # Explicitly use stdout
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] - %(levelname)s: [%(name)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )
        uvicorn_access_logger.addHandler(handler)
        uvicorn_access_logger.propagate = False  # Prevent propagation to root logger
        logging.getLogger(__name__).info("Uvicorn access logger format configured.")
    except ModuleNotFoundError:
        logging.getLogger(__name__).warning(
            "Uvicorn not found, skipping access logger configuration."
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error configuring uvicorn logger: {e}", exc_info=True
        )


def setup_logging():
    """Configures basic logging and the uvicorn access logger."""
    log_level_int = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level_int,
        format="[%(asctime)s] - %(levelname)s: [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        stream=sys.stdout,  # Explicitly use stdout
        force=True,  # Override any existing root logger config
    )
    # Set httpx log level higher to reduce noise, unless debug is enabled
    if log_level_int > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)

    configure_uvicorn_logger()
    logging.getLogger(__name__).info(f"Logging configured with level: {LOG_LEVEL}")
