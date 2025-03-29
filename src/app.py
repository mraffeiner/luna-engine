from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
import openai
from groq import Groq
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en"
DEFAULT_FORMAT = "json"
DEFAULT_PROMPT = "Transcribe all verbalized filler words like 'um,' 'uh,' and 'like' exactly as spoken, preserving speech patterns including pauses and repetitions or even complete silence with *silence* or noise with *noise*"


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
    title="STT Service API",
    description="Speech-to-Text service using OpenAI's Whisper API and Groq's Whisper API",
    lifespan=lifespan,
)

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY environment variable not set.")

# Load Groq API key and initialize client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
if not groq_client.api_key:
    logger.warning("GROQ_API_KEY environment variable not set.")

# Define available models
OPENAI_MODELS = {
    "whisper-1": "OpenAI Whisper",
    "gpt-4o-transcribe": "GPT-4o Transcribe",
}
GROQ_MODELS = {
    "whisper-large-v3": "Groq Whisper Large v3",
    "whisper-large-v3-turbo": "Groq Whisper Large Turbo v3",
    "distil-whisper-large-v3-en": "Groq Distil Whisper English",
}


# API Models
class SttResponse(BaseModel):
    text: str


# API Endpoints
@app.get("/health", summary="Health check endpoint")
async def health_check():
    status = "ok"
    warnings = []

    if not openai.api_key:
        warnings.append("OPENAI_API_KEY not set")
        status = "warning"

    if not groq_client.api_key:
        warnings.append("GROQ_API_KEY not set")
        status = "warning"

    return {
        "status": status,
        "warnings": warnings if warnings else None,
    }


@app.get("/models", summary="Get available STT models")
async def get_models():
    available_models = []

    # Add OpenAI models if API key is available
    if openai.api_key:
        logger.info("OpenAI API key is available, adding OpenAI models")
        for model_id, model_name in OPENAI_MODELS.items():
            available_models.append({"value": model_id, "label": model_name})
            logger.info(f"Added OpenAI model: {model_id} ({model_name})")
    else:
        logger.warning("OpenAI API key is not available, skipping OpenAI models")

    # Add Groq models if API key is available
    if groq_client.api_key:
        logger.info("Groq API key is available, adding Groq models")
        for model_id, model_name in GROQ_MODELS.items():
            available_models.append({"value": model_id, "label": model_name})
            logger.info(f"Added Groq model: {model_id} ({model_name})")
    else:
        logger.warning("Groq API key is not available, skipping Groq models")

    logger.info(f"Returning {len(available_models)} available models")
    return {"models": available_models}


async def transcribe_with_openai(audio_path: str, model: str = "whisper-1") -> str:
    """Transcribe audio using OpenAI's Whisper API."""
    try:
        with open(audio_path, "rb") as audio_file:
            result = openai.audio.transcriptions.create(
                model=model,
                file=audio_file,
                # language=DEFAULT_LANGUAGE,
                response_format=DEFAULT_FORMAT,
                prompt=DEFAULT_PROMPT,
            )
        logger.info(f"OpenAI transcription successful with model {model}")
        return result.text
    except Exception:
        logger.exception(f"Unexpected error during transcription with OpenAI {model}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transcription with OpenAI API {model}",
        )


async def transcribe_with_groq(audio_path: str, model: str = "whisper-large-v3") -> str:
    """Transcribe audio using Groq's Whisper API."""
    try:
        with open(audio_path, "rb") as audio_file:
            result = groq_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                # language=DEFAULT_LANGUAGE,
                response_format=DEFAULT_FORMAT,
                prompt=DEFAULT_PROMPT,
            )
        logger.info(f"Groq transcription successful with model {model}")
        return result.text
    except Exception:
        logger.exception(f"Unexpected error during transcription with Groq {model}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transcription with Groq {model}",
        )


@app.post("/transcribe", response_model=SttResponse, summary="Transcribe audio to text")
async def stt_endpoint(
    audio: UploadFile = File(...),
    model: str = Form("whisper-large-v3"),
):
    """
    Transcribe audio file to text using OpenAI's Whisper API or Groq's Whisper API.

    Accepts audio files in various formats (mp3, wav, m4a, etc.)
    """
    # Check if the model is available
    if model in OPENAI_MODELS and not openai.api_key:
        raise HTTPException(
            status_code=500, detail="OpenAI API key not configured on the server"
        )
    elif model in GROQ_MODELS and not groq_client.api_key:
        raise HTTPException(
            status_code=500, detail="Groq API key not configured on the server"
        )
    elif model not in OPENAI_MODELS and model not in GROQ_MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_filename = temp_file.name
            # Write the uploaded file content to the temporary file
            content = await audio.read()
            temp_file.write(content)

        # Transcribe the audio using the appropriate API
        try:
            if model in OPENAI_MODELS:
                result = await transcribe_with_openai(temp_filename, model)
            elif model in GROQ_MODELS:
                result = await transcribe_with_groq(temp_filename, model)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

            return SttResponse(text=result)
        finally:
            # Always clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    except Exception:
        logger.exception(f"Unexpected error during transcription")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error during transcription"
        )
