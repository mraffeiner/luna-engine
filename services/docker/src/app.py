import asyncio
from contextlib import asynccontextmanager
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import logging
import aiodocker
from pydantic import BaseModel

# Constants
DOCKER_TIMEOUT = 30

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

active_log_tasks = []
docker_log_client = None


# Only containers of this compose project may be inspected, started or stopped.
# The Docker socket gives root-equivalent access to the host, so never act on arbitrary containers.
COMPOSE_PROJECT = "luna-engine"
COMPOSE_PROJECT_LABEL = "com.docker.compose.project"


async def get_project_container(docker_client: aiodocker.Docker, container_name: str):
    """Return the container and its info, or raise 404 if it isn't part of the Luna Engine project."""
    try:
        container = await docker_client.containers.get(container_name)
    except aiodocker.DockerError as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404, detail=f"Container '{container_name}' not found"
            )
        raise
    container_info = await container.show()
    labels = container_info.get("Config", {}).get("Labels") or {}
    if labels.get(COMPOSE_PROJECT_LABEL) != COMPOSE_PROJECT:
        logger.warning(
            f"Refusing to act on '{container_name}': not part of the {COMPOSE_PROJECT} project"
        )
        raise HTTPException(
            status_code=404, detail=f"Container '{container_name}' not found"
        )
    return container, container_info


# Models
class ContainerStatusResponse(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] - %(levelname)s: %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )
    )
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(handler)
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Docker Service API",
    description="Docker Service for managing containers and streaming logs",
    lifespan=lifespan,
)
load_dotenv()


# API endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


@app.get("/container_status/{container_name}", response_model=ContainerStatusResponse)
async def get_container_status(container_name: str):
    docker_client = aiodocker.Docker()

    try:
        container, container_info = await get_project_container(
            docker_client, container_name
        )
        return ContainerStatusResponse(
            status=container_info.get("State", {}).get("Status")
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            f"Unexpected error getting container status for {container_name}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error getting container status for {container_name}",
        )
    finally:
        await docker_client.close()


@app.post("/start_container/{container_name}")
async def start_container(container_name: str):
    docker_client = aiodocker.Docker()

    try:
        container, container_info = await get_project_container(
            docker_client, container_name
        )
        status = container_info.get("State", {}).get("Status")
        if status == "created" or status == "exited":
            logger.info(f"Starting container '{container_name}'..")
            await container.start(timeout=DOCKER_TIMEOUT)
            logger.info(f"Container '{container_name}' started successfully")

            return JSONResponse(
                status_code=200,
                content=f"Container '{container_name}' started successfully",
            )
        elif status == "running" or status == "restarting":
            logger.info(
                f"Container '{container_name}' is running or currently restarting"
            )
            return JSONResponse(status_code=200, content="Container is already running")
        elif status == "paused":
            logger.info(f"Container '{container_name}' was paused, unpausing..")
            await container.unpause()
            logger.info(f"Container '{container_name}' successully unpaused")
            return JSONResponse(
                status_code=200,
                content=f"Container '{container_name}' was paused and has now been unpaused",
            )
        elif status == "dead":
            logger.error(f"Container '{container_name}' is dead and cannot be started")
            return JSONResponse(
                status_code=500, content=f"Container '{container_name}' is dead"
            )
        else:
            raise Exception(f"Unknown container status: {status}")
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Unexpected error starting container {container_name}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error starting container {container_name}",
        )
    finally:
        await docker_client.close()


@app.post("/stop_container/{container_name}")
async def stop_container(container_name: str):
    docker_client = aiodocker.Docker()

    try:
        container, container_info = await get_project_container(
            docker_client, container_name
        )
        status = container_info.get("State", {}).get("Status")
        if status == "running" or status == "restarting":
            logger.info(f"Stopping container '{container_name}'..")
            await container.stop(timeout=DOCKER_TIMEOUT)
            logger.info(f"Container '{container_name}' stopped successfully")
            return JSONResponse(
                status_code=200,
                content=f"Container '{container_name}' stopped successfully",
            )
        elif status == "exited" or status == "created" or status == "paused":
            logger.info(f"Container '{container_name}' is already stopped")
            return JSONResponse(status_code=200, content="Container is already stopped")
        elif status == "dead":
            logger.warning(f"Can't stop a dead container '{container_name}'")
            return JSONResponse(status_code=200, content="Container is dead")
        else:
            raise Exception(f"Unknown container status: {status}")
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Unexpected error stopping container {container_name}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error stopping container {container_name}",
        )
    finally:
        await docker_client.close()


@app.get("/container_logs")
async def get_container_logs():
    global active_log_tasks, docker_log_client

    if docker_log_client:
        logger.warning("Only one docker log client is allowed at a time. Closing..")
        await docker_log_client.close()
        logger.info("Docker client closed")

    logger.info("Creating new docker log client")
    docker_log_client = aiodocker.Docker()
    queue = asyncio.Queue()

    async def stream_container_logs(container):
        while container:
            try:
                container_info = await container.show()
                name = container_info.get("Name", "Unknown").lstrip("/")
                status = container_info.get("State", {}).get("Status")
                logger.info(f"Starting log stream for {status} container {name}")

                if status == "dead":
                    logger.error(f"Container {name} is dead, terminating log stream")
                    break
                elif status != "running":
                    logger.info(
                        f"Container {name} is not currently running. Skipping log stream for 30s"
                    )
                    await asyncio.sleep(30)
                    continue

                async for log in container.log(
                    stdout=True, stderr=True, follow=True, tail=100
                ):
                    data = {"service": name, "log": log.strip()}
                    await queue.put(f"data: {json.dumps(data)}\n\n")

                logger.warning(f"Log stream paused for {name}. Resuming in 5s")
                await asyncio.sleep(5)

            except asyncio.TimeoutError:
                logger.warning(f"Continuing log stream for {name} after timeout")
            except asyncio.CancelledError:
                logger.warning(f"Log stream for {name} cancelled")
                raise
            except Exception:
                logger.error(f"Error streaming logs for {name}")
                raise

        logger.error(f"Lost container {name} during log stream")

    async def heartbeat():
        logger.info("Heartbeat task for log stream started")
        while True:
            await asyncio.sleep(30)
            logger.info("Log stream heartbeat")

    async def stream_logs():
        global active_log_tasks, docker_log_client

        try:
            # Create log task for heartbeat
            heartbeat_task = asyncio.create_task(heartbeat())
            active_log_tasks.append(heartbeat_task)

            # Create log task for each container on the network
            logger.info("Getting list of containers on the network")
            containers = await docker_log_client.containers.list(
                filters={"network": ["luna-engine_default"]}
            )
            logger.info(f"Found {len(containers)} containers on luna-engine_default")

            logger.info("Creating log tasks for each container")
            for container in containers:
                task = asyncio.create_task(stream_container_logs(container))
                active_log_tasks.append(task)
            logger.info(f"Log tasks successfully created")

            # Continue yielding logs as they become available
            while True:
                log_data = await queue.get()
                yield log_data
        except asyncio.CancelledError:
            logger.warning("Log stream cancelled")
        except Exception:
            logger.exception("Unexpected error streaming logs")
            raise HTTPException(
                status_code=500, detail="Unexpected error streaming logs"
            )
        finally:
            # Cancel all log tasks
            logger.info("Finally cancelling log tasks")
            for task in active_log_tasks:
                task.cancel()
            active_log_tasks.clear()
            logger.info("Log tasks fnally cancelled")

    logger.info("Starting log streams")
    return StreamingResponse(stream_logs(), media_type="text/event-stream")
