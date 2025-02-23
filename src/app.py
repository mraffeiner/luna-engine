from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import logging
import docker
import httpx
from pydantic import BaseModel


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


class LLMRequest(BaseModel):
    model: str
    prompt: str


@app.post("/llm/chat")
async def llm_chat(request: LLMRequest = Body()):
    async def stream_response():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST", "http://llm-service:5001/chat", json=request.model_dump()
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
            except httpx.HTTPError as e:
                logging.error(f"Error proxying to llm-service: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to communicate with llm-service",
                )

    return StreamingResponse(stream_response(), media_type="text/event-stream")


class TTSRequest(BaseModel):
    language: str
    voice: str
    style: str
    rate: str
    pitch: str
    text: str


@app.post("/tts/speech")
async def tts_speech(request: TTSRequest = Body()):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://tts-service:5002/tts", json=request.model_dump()
            )
            return Response(content=response.content, media_type="audio/wav")
        except httpx.HTTPError as e:
            logging.error(f"Error proxying to tts-service: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to communicate with tts-service",
            )
