import asyncio
from fastapi import Body, FastAPI, File, HTTPException, Response, UploadFile, WebSocket
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import logging
import aiodocker
import httpx
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal
import websockets

# Constants
DOCKER_TIMEOUT = 30
CONTROL_PANEL_BACKEND_URL = "http://control-panel-backend:5000"
LLM_SERVICE_URL = "http://llm-service:5001"
TTS_SERVICE_URL = "http://tts-service:5002"
STT_SERVICE_URL = "http://stt-service:5003"
DISCORD_SERVICE_URL = "http://discord-service:5004"
DISCORD_SERVICE_WS_URL = "ws://discord-service:5004"

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


class TTSEngine(str, Enum):
    """Supported TTS engines"""

    AZURE = "azure"
    KOKORO = "kokoro"


class BaseTTSRequest(BaseModel):
    """Base model for TTS synthesis requests"""

    language: str = Field(..., description="Language code (e.g., en-US)")
    voice: str = Field(..., description="Voice identifier")
    text: str = Field(..., description="Text to synthesize")


class AzureTTSRequest(BaseTTSRequest):
    """Azure-specific TTS request model"""

    engine: Literal[TTSEngine.AZURE] = TTSEngine.AZURE
    style: str = Field("default", description="Speaking style")
    rate: str = Field("0%", description="Speaking rate (-100% to 100%)")
    pitch: str = Field("0%", description="Voice pitch (-100% to 100%)")


class KokoroTTSRequest(BaseTTSRequest):
    """Kokoro-specific TTS request model"""

    engine: Literal[TTSEngine.KOKORO] = TTSEngine.KOKORO
    speed: float = Field(1.0, description="Speaking speed multiplier (0.5-2.0)")
    pitch: float = Field(1.0, description="Voice pitch multiplier (0.5-2.0)")


# Union type for request validation
TTSRequest = AzureTTSRequest | KokoroTTSRequest

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
        # Convert the request to a dict for sending to the TTS service
        request_data = request.model_dump()

        # Log the request type for debugging
        logger.info(
            f"Processing TTS request for engine: {request_data.get('engine', 'unknown')}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TTS_SERVICE_URL}/tts", json=request_data, timeout=30.0
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TTS_SERVICE_URL}/options", timeout=5.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_detail = (
            f"TTS service error: {e.response.text[:200] if e.response.text else str(e)}"
        )
        logger.error(error_detail)
        raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Error fetching TTS options: {e}")
        raise HTTPException(status_code=500, detail=f"Error in TTS service: {str(e)}")


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


@app.post("/stt")
async def stt_proxy(audio: UploadFile = File(...)):
    """
    Proxy endpoint for the STT service.
    Accepts an audio file upload and forwards it to the STT service.
    """
    try:
        # Read the file content
        audio_content = await audio.read()

        async with httpx.AsyncClient() as client:
            # Forward the file to the STT service
            files = {"audio": (audio.filename, audio_content, audio.content_type)}

            response = await client.post(
                f"{STT_SERVICE_URL}/stt", files=files, timeout=30.0
            )

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            error_detail = e.response.json()
            logger.error(f"STT service error: {error_detail}")
            raise HTTPException(status_code=status_code, detail=error_detail)
        except:
            error_detail = f"STT service error: {str(e)}"
            logger.error(error_detail)
            raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Error in STT service: {e}")
        raise HTTPException(status_code=500, detail=f"Error in STT service: {str(e)}")


@app.post("/discord/join-voice")
async def discord_join_voice(request: dict = Body(...)):
    """
    Proxy endpoint to join a Discord voice channel.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DISCORD_SERVICE_URL}/join-voice", json=request, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_detail = f"Discord service error: {e.response.text[:200] if e.response.text else str(e)}"
        logger.error(error_detail)
        raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Error in Discord service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error in Discord service: {str(e)}"
        )


@app.post("/discord/leave-voice")
async def discord_leave_voice(request: dict = Body(...)):
    """
    Proxy endpoint to leave a Discord voice channel.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DISCORD_SERVICE_URL}/leave-voice", json=request, timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_detail = f"Discord service error: {e.response.text[:200] if e.response.text else str(e)}"
        logger.error(error_detail)
        raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"Error in Discord service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error in Discord service: {str(e)}"
        )


@app.websocket("/discord/ws")
async def websocket_proxy(frontend_websocket: WebSocket):
    await frontend_websocket.accept()

    try:
        async with websockets.connect(f"{DISCORD_SERVICE_WS_URL}") as backend_socket:
            backend_websocket = backend_socket

            async def forward_to_backend():
                while frontend_websocket.state == websockets.protocol.State.OPEN:
                    data = await frontend_websocket.receive_bytes()
                    await backend_socket.send(data)

            async def forward_to_frontend():
                while backend_socket.state == websockets.protocol.State.OPEN:
                    data = await backend_socket.recv()
                    await frontend_websocket.send_bytes(data)

            await asyncio.gather(forward_to_backend(), forward_to_frontend())
    except websockets.ConnectionClosedOK:
        logger.info("WebSocket connection closed normally")
    except websockets.ConnectionClosed:
        logger.warning("WebSocket connection closed unexpectedly")
    except Exception as e:
        logger.error(f"Error in WebSocket proxy: {e}")
    finally:
        await frontend_websocket.close()
        await backend_websocket.close()
