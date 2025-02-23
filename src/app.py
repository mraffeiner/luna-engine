from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import logging
import docker


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


app = FastAPI()

load_dotenv()

client = docker.from_env()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/start_container/{container_name}")
async def start_container(container_name: str):
    try:
        container = client.containers.get(container_name)
        if container.status != "running":
            container.start()
            logging.info(f"Container '{container_name}' started successfully")
            return {"message": f"Container '{container_name}' started successfully"}
        else:
            logging.info(f"Container '{container_name}' is already running")
            return {"message": f"Container '{container_name}' is already running"}
    except docker.errors.NotFound as e:
        logging.error(f"Error starting container '{container_name}': {e}")
        raise HTTPException(
            status_code=404, detail=f"Container '{container_name}' not found"
        )
    except docker.errors.APIError as e:
        logging.error(f"Docker API error starting container '{container_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start container '{container_name}'"
        )
    except Exception as e:
        logging.error(f"Unexpected error starting container '{container_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start container '{container_name}'"
        )


@app.post("/stop_container/{container_name}")
async def stop_container(container_name: str):
    try:
        container = client.containers.get(container_name)
        if container.status == "running":
            container.stop()
            logging.info(f"Container '{container_name}' stopped successfully")
            return {"message": f"Container '{container_name}' stopped successfully"}
        else:
            logging.info(f"Container '{container_name}' is not running")
            return {"message": f"Container '{container_name}' is not running"}
    except docker.errors.NotFound as e:
        logging.error(f"Error stopping container '{container_name}': {e}")
        raise HTTPException(
            status_code=404, detail=f"Container '{container_name}' not found"
        )
    except docker.errors.APIError as e:
        logging.error(f"Docker API error stopping container '{container_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop container {container_name}"
        )
    except Exception as e:
        logging.error(f"Unexpected error stopping container '{container_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop container '{container_name}'"
        )
