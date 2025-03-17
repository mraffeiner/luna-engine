from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import openai
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] - %(levelname)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
    )
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(handler)
    yield


# Initialize FastAPI app
app = FastAPI(
    title="STT Service API",
    description="Speech-to-Text service using OpenAI's Whisper API",
    lifespan=lifespan,
)

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY environment variable not set.")


# API Models
class SttResponse(BaseModel):
    text: str


# API Endpoints
@app.get("/health", summary="Health check endpoint")
async def health_check():
    if not openai.api_key:
        return {
            "status": "warning",
            "message": "OPENAI_API_KEY not set",
        }
    return {"status": "ok"}


@app.post("/transcribe", response_model=SttResponse, summary="Transcribe audio to text")
async def stt_endpoint(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using OpenAI's Whisper API.

    Accepts audio files in various formats (mp3, wav, m4a, etc.)
    """
    if not openai.api_key:
        raise HTTPException(
            status_code=500, detail="OpenAI API key not configured on the server"
        )

    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_filename = temp_file.name
            # Write the uploaded file content to the temporary file
            content = await audio.read()
            temp_file.write(content)

        # Transcribe the audio using OpenAI API
        try:
            with open(temp_filename, "rb") as audio_file:
                result = openai.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", response_format="text"
                )

            logger.info(f"Transcription successful")
            return SttResponse(text=result)
        finally:
            # Always clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    except openai.APIError:
        logger.exception("OpenAI API error")
        raise HTTPException(
            status_code=500, detail=f"OpenAI API error during transcription"
        )
    except Exception:
        logger.exception("Unexpected error during transcription")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error during transcription"
        )
