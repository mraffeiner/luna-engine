import asyncio
from fastapi import Body, FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
import logging
import aiodocker
import httpx
from pydantic import BaseModel, Field

# Constants
DOCKER_TIMEOUT = 30
CONTROL_PANEL_BACKEND_URL = "http://control-panel-backend:5000"
LLM_SERVICE_URL = "http://llm-service:5001"
TTS_SERVICE_URL = "http://tts-service:5002"

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


class LLMRequest(BaseModel):
    model: str = Field(..., description="The LLM model to use")
    prompt: str = Field(..., description="The prompt to send to the model")


class TTSRequest(BaseModel):
    language: str = Field(..., description="The language for TTS")
    voice: str = Field(..., description="The voice to use")
    style: str = Field(..., description="The speaking style")
    rate: str = Field(..., description="The speaking rate")
    pitch: str = Field(..., description="The voice pitch")
    text: str = Field(..., description="The text to convert to speech")


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


@app.post("/llm/chat")
async def llm_chat(request: LLMRequest = Body(...)):
    async def stream_response():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{LLM_SERVICE_URL}/chat",
                    json=request.model_dump(),
                    timeout=30.0,
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
            except Exception as e:
                logger.error(f"Error in LLM service: {e}")
                yield f'event: error\ndata: {{"status": 500, "message": "Error in LLM service: {str(e)}"}}\n\n'

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@app.post("/tts/speech")
async def tts_speech(request: TTSRequest = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TTS_SERVICE_URL}/tts", json=request.model_dump(), timeout=30.0
            )
            response.raise_for_status()
            return Response(content=response.content, media_type="audio/wav")
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_detail = (
            f"TTS service error: {e.response.text[:200] if e.response.text else str(e)}"
        )
        logger.error(error_detail)
        raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Error in TTS service: {e}")
        raise HTTPException(status_code=500, detail=f"Error in TTS service: {str(e)}")


@app.get("/tts/options")
async def get_tts_options():
    return {
        "languages": [
            {"value": "en-US", "label": "English (US)"},
            {"value": "en-GB", "label": "English (GB)"},
            {"value": "fr-FR", "label": "French (France)"},
            {"value": "es-ES", "label": "Spanish (Spain)"},
            {"value": "de-DE", "label": "German (Germany)"},
        ],
        "voices": [
            {"value": "en-US-AriaNeural", "label": "Aria (en-US)"},
            {"value": "en-US-GuyNeural", "label": "Guy (en-US)"},
            {"value": "en-US-NancyNeural", "label": "Nancy (en-US)"},
            {"value": "en-GB-MiaNeural", "label": "Mia (en-GB)"},
            {"value": "fr-FR-HenriNeural", "label": "Henri (fr-FR)"},
            {"value": "es-ES-ElviraNeural", "label": "Elvira (es-ES)"},
            {"value": "de-DE-KatjaNeural", "label": "Katja (de-DE)"},
        ],
        "styles": [
            {"value": "default", "label": "Default"},
            {"value": "cheerful", "label": "Cheerful"},
            {"value": "sad", "label": "Sad"},
            {"value": "angry", "label": "Angry"},
            {"value": "whispering", "label": "Whispering"},
        ],
    }


@app.get("/llm/options")
async def get_llm_options():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{LLM_SERVICE_URL}/models")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = f"LLM service error: {e.response.text[:200] if e.response.text else str(e)}"
            logger.error(error_detail)
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            logger.error(f"Error in LLM service: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error in LLM service: {str(e)}"
            )
