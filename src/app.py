import asyncio
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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

active_log_streams = {}


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
    except Exception as e:
        logger.error(f"Error getting container status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        logger.error(f"Error starting container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        logger.error(f"Error stopping container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/container_logs/{container_name}")
async def get_container_logs(container_name: str):
    global active_log_streams

    if container_name not in active_log_streams:
        active_log_streams[container_name] = 0

    async def stream_logs(container_name):
        try:
            container = await docker_client.containers.get(container_name)
            log_iterator = container.log(stdout=True, stderr=True, follow=True, tail=10)

            active_log_streams[container_name] += 1
            id = active_log_streams[container_name]

            async for log in log_iterator:
                yield f"data: {log.strip()}\n\n"
                if id != active_log_streams[container_name]:
                    break
        except asyncio.exceptions.CancelledError:
            logger.error(f"Log stream for {container_name} cancelled.")
        except asyncio.exceptions.TimeoutError:
            logger.error(f"Log stream for {container_name} timed out.")
        except Exception as e:
            logger.error(f"Unexpected error during log stream for {container_name}:", e)
        finally:
            logger.info(f"Log stream for {container_name} closed.")

    return StreamingResponse(
        stream_logs(container_name), media_type="text/event-stream"
    )
