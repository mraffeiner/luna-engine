import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
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
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

active_log_tasks = None


# Models
class ContainerStatusResponse(BaseModel):
    running: bool
    status: str


class ContainerResponse(BaseModel):
    message: str


# Initialize FastAPI and Docker client
app = FastAPI(title="Luna Engine Control Panel")
load_dotenv()
docker_client = aiodocker.Docker()


# API endpoints
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/container_status/{container_name}", response_model=ContainerStatusResponse)
async def get_container_status(container_name: str):
    try:
        container = await docker_client.containers.get(container_name)
        container_info = await container.show()
        status = container_info.get("State", {}).get("Status")
        return ContainerStatusResponse(
            running=status == "running",
            status=status,
        )
    except Exception:
        logger.exception(
            f"Unexpected error getting container status for {container_name}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error getting container status for {container_name}",
        )


@app.post("/start_container/{container_name}", response_model=ContainerResponse)
async def start_container(container_name: str):
    try:
        container = await docker_client.containers.get(container_name)
        container_info = await container.show()
        status = container_info.get("State", {}).get("Status")
        if status != "running":
            await container.start()
            logger.info(f"Container '{container_name}' started successfully")
            return ContainerResponse(
                message=f"Container '{container_name}' started successfully"
            )
        return ContainerResponse(
            message=f"Container '{container_name}' is already running"
        )
    except Exception:
        logger.exception(f"Unexpected error starting container {container_name}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error starting container {container_name}",
        )


@app.post("/stop_container/{container_name}", response_model=ContainerResponse)
async def stop_container(container_name: str):
    try:
        container = await docker_client.containers.get(container_name)
        container_info = await container.show()
        status = container_info.get("State", {}).get("Status")
        if status == "running":
            await container.stop(timeout=DOCKER_TIMEOUT)
            logger.info(f"Container '{container_name}' stopped successfully")
            return ContainerResponse(
                message=f"Container '{container_name}' stopped successfully"
            )
        return ContainerResponse(message=f"Container '{container_name}' is not running")
    except Exception:
        logger.exception(f"Unexpected error stopping container {container_name}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error stopping container {container_name}",
        )


@app.get("/container_logs")
async def get_container_logs():
    global active_log_tasks

    if active_log_tasks:
        logger.warning(
            f"Only one log stream is allowed at a time. Cancelling previous log stream."
        )
        for task in active_log_tasks:
            task.cancel()

    active_log_tasks = []
    queue = asyncio.Queue()

    async def stream_container_logs(container):
        try:
            container_info = await container.show()
            name = container_info.get("Name", "Unknown").lstrip("/")
            async for log in container.log(
                stdout=True, stderr=True, follow=True, tail=10
            ):
                data = {"service": name, "log": log.strip()}
                await queue.put(f"data: {json.dumps(data)}\n\n")
        except asyncio.CancelledError:
            logger.error(f"Log stream for container {name} cancelled.")
            raise
        except Exception:
            logger.exception(f"Unexpected error during log stream for container {name}")

    async def stream_logs():
        global active_log_tasks

        try:
            containers = await docker_client.containers.list(
                filters={"network": ["luna-engine_default"]}
            )
            # Spawn a task for each container
            for container in containers:
                task = asyncio.create_task(stream_container_logs(container))
                active_log_tasks.append(task)

            # Continue yielding logs as they become available
            while True:
                log_data = await queue.get()
                yield log_data
        except asyncio.CancelledError:
            for task in active_log_tasks:
                task.cancel()
            raise
        finally:
            logger.info("Log stream closed.")

    return StreamingResponse(stream_logs(), media_type="text/event-stream")
