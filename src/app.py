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


@app.post("/start_service/{service_name}")
async def start_service(service_name: str):
    try:
        container = client.containers.get(service_name)
        if container.status != "running":
            container.start()
            return {"message": f"Service '{service_name}' started successfully"}
        else:
            return {"message": f"Service '{service_name}' is already running"}
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )
    except docker.errors.APIError as e:
        logging.error(f"Docker API error starting service '{service_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")
    except Exception as e:
        logging.error(f"Error starting service '{service_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start service '{service_name}': {e}"
        )


@app.post("/stop_service/{service_name}")
async def stop_service(service_name: str):
    try:
        container = client.containers.get(service_name)
        if container.status == "running":
            container.stop()
            return {"message": f"Service '{service_name}' stopped successfully"}
        else:
            return {"message": f"Service '{service_name}' is not running"}
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )
    except docker.errors.APIError as e:
        logging.error(f"Docker API error stopping service '{service_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Docker API error: {e}")
    except Exception as e:
        logging.error(f"Error stopping service '{service_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop service '{service_name}': {e}"
        )
