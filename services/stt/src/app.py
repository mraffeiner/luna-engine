from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from datetime import datetime

from pydantic import BaseModel
import openai
from groq import Groq
import os
import logging
import tempfile
import subprocess
import wave
from array import array
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Reverted level back to INFO
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en"
DEFAULT_FORMAT = "json"
DEFAULT_PROMPT = "Transcribe all verbalized filler words like 'um,' 'uh,' and 'like' exactly as spoken, preserving speech patterns including pauses and repetitions (example: Um.. I-I don't think it, uh, like.. works that way)"


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

    # Load Silero VAD model
    try:
        global vad_model, get_speech_timestamps, collect_chunks
        torch.set_num_threads(1)
        vad_model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False, trust_repo=True
        )
        # Silero's read_audio/save_audio need a torchaudio backend, so audio I/O
        # goes through ffmpeg and the wave module instead (see decode_audio/write_wav).
        (get_speech_timestamps, _, _, _, collect_chunks) = utils
        logger.info("Silero VAD model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Silero VAD model: {e}")
        vad_model = None  # Indicate model loading failure
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
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


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


TARGET_SAMPLE_RATE = 16000


def decode_audio(path: str) -> torch.Tensor:
    """Decode any format ffmpeg reads (webm, mp3, wav...) to mono float32 at TARGET_SAMPLE_RATE."""
    proc = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-v", "error", "-i", path,
            "-f", "f32le", "-ac", "1", "-ar", str(TARGET_SAMPLE_RATE), "-",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed to decode {path}: {proc.stderr.decode(errors='replace').strip()}"
        )
    if not proc.stdout:
        return torch.zeros(0)
    return torch.frombuffer(bytearray(proc.stdout), dtype=torch.float32)


def write_wav(path: str, audio: torch.Tensor) -> None:
    """Write a mono float tensor as 16-bit PCM WAV at TARGET_SAMPLE_RATE."""
    pcm = (audio.clamp(-1.0, 1.0) * 32767).to(torch.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(TARGET_SAMPLE_RATE)
        f.writeframes(array("h", pcm.tolist()).tobytes())


async def extract_speech_only(
    input_audio_path: str, output_dir: str = "."
) -> Optional[str]:
    """
    Applies Silero VAD to an audio file and saves only speech segments.

    If no speech is detected, returns None. Otherwise, returns the path
    to the output audio file containing only speech segments.

    Uses the Silero 'vad_model', 'get_speech_timestamps' and 'collect_chunks'
    loaded in lifespan.

    Args:
        input_audio_path: Path to the input audio file.
        output_dir: Directory to save the output file. Defaults to current dir.

    Returns:
        Optional[str]: Path to the output audio file if speech is detected,
                       otherwise None.

    Raises:
        FileNotFoundError: If the input audio file does not exist.
        Exception: If VAD processing or audio saving fails (other than no speech).
    """
    if not os.path.exists(input_audio_path):
        raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")

    try:
        # 1. Decode and resample to mono TARGET_SAMPLE_RATE with ffmpeg
        wav = decode_audio(input_audio_path)

        # 2. Get speech timestamps from the VAD model
        # You can tweak parameters like threshold, min_speech_duration_ms, etc.
        speech_timestamps = get_speech_timestamps(
            wav, vad_model, sampling_rate=TARGET_SAMPLE_RATE, min_speech_duration_ms=100
        )

        # --- Check if any speech was detected ---
        if not speech_timestamps:
            print(
                f"Warning: No speech detected in {input_audio_path}. Skipping file creation."
            )
            return None  # Return None if no speech found
        # ----------------------------------------

        # 3. Collect audio chunks corresponding to speech timestamps
        # This will only run if speech_timestamps is not empty
        speech_audio = collect_chunks(speech_timestamps, wav)

        # --- Double-check collected audio tensor is not empty ---
        # Although collect_chunks should return data if timestamps exist,
        # this is an extra safety measure.
        if speech_audio.numel() == 0:
            print(
                f"Warning: Speech timestamps found, but collected audio is empty for {input_audio_path}. Skipping file creation."
            )
            return None
        # -------------------------------------------------------

        # 4. Define output path and ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        base, _ = os.path.splitext(os.path.basename(input_audio_path))
        output_audio_path = os.path.join(output_dir, f"{base}_speech_only.wav")

        # 5. Save the concatenated speech segments
        write_wav(output_audio_path, speech_audio)

        # 6. Basic check if file was created and has some size (more than header)
        # A typical WAV header is 44 bytes. Anything larger means audio data exists.
        try:
            if os.path.getsize(output_audio_path) > 44:
                return output_audio_path
            else:
                print(
                    f"Warning: Output file {output_audio_path} seems empty (only header). Skipping."
                )
                # Optionally remove the empty file
                # os.remove(output_audio_path)
                return None
        except OSError as e:
            print(
                f"Warning: Could not check size of output file {output_audio_path}: {e}"
            )
            # Decide if you still want to return the path or None
            return None

    except Exception as e:
        print(f"Error processing {input_audio_path}: {e}")
        # Re-raise the exception for the caller to handle if needed
        raise


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

    temp_filename = None
    vad_processed_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_filename = temp_file.name
            content = await audio.read()
            if not content:
                raise HTTPException(
                    status_code=400, detail="Received empty audio file."
                )
            temp_file.write(content)
            logger.info(f"Saved uploaded audio to temporary file: {temp_filename}")

        vad_processed_path = await extract_speech_only(temp_filename)
        if not vad_processed_path:
            logger.warning(
                f"No speech detected in {temp_filename}. Skipping transcription."
            )
            return SttResponse(text="*noises*")

        if model in OPENAI_MODELS:
            result = await transcribe_with_openai(vad_processed_path, model)
        elif model in GROQ_MODELS:
            result = await transcribe_with_groq(vad_processed_path, model)
        else:
            # Should not happen due to earlier checks
            raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

        return SttResponse(text=result)

    except Exception as e:  # Capture exception to potentially re-raise
        logger.exception("Unexpected error during transcription process")
        # Re-raise HTTPException if it's already one, otherwise wrap
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500, detail="Unexpected error during transcription"
            )

    finally:
        # Clean up VAD file first (as it might be the same as temp_filename if VAD failed/skipped)
        if vad_processed_path and os.path.exists(vad_processed_path):
            # Avoid double deletion if VAD returned the original path
            if vad_processed_path != temp_filename:
                os.remove(vad_processed_path)
                logger.info(f"Cleaned up VAD processed file: {vad_processed_path}")
            else:
                logger.info(
                    f"VAD processed path is same as temp path ({vad_processed_path}), skipping separate deletion."
                )

        # Clean up the main temporary file
        if temp_filename and os.path.exists(temp_filename):
            # Check again in case it was the same as vad_processed_path and already deleted
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                logger.info(f"Cleaned up temporary file: {temp_filename}")
            else:
                logger.info(
                    f"Temporary file ({temp_filename}) was already cleaned up (likely same as VAD path)."
                )
