from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Body, Response, HTTPException
from pydantic import BaseModel, Field
import azure.cognitiveservices.speech as speechsdk
import os
import httpx
from dotenv import load_dotenv
import logging
import struct
from enum import Enum
from typing import List, Dict, Literal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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
    title="TTS Service API",
    description="Text-to-Speech service supporting multiple engines",
    lifespan=lifespan,
)

# Load environment variables
load_dotenv()


# TTS Engine configuration
class TTSEngine(str, Enum):
    """Supported TTS engines"""

    AZURE = "azure"
    KOKORO = "kokoro"
    SESAME = "sesame"


# Azure TTS configuration
azure_speech_config = None
if os.getenv("AZURE_SUBSCRIPTION") and os.getenv("AZURE_ENDPOINT"):
    azure_speech_config = speechsdk.SpeechConfig(
        subscription=os.getenv("AZURE_SUBSCRIPTION"),
        endpoint=os.getenv("AZURE_ENDPOINT"),
    )
    azure_speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm
    )

# Kokoro TTS configuration
KOKORO_API_URL = os.getenv("KOKORO_API_URL", "http://kokoro-tts:8880")
SESAME_API_URL = os.getenv("SESAME_API_URL", "http://sesame-tts:8000")


# API Models
class BaseTTSRequest(BaseModel):
    """Base model for TTS synthesis requests"""

    voice: str = Field(..., description="Voice identifier")
    text: str = Field(..., description="Text to synthesize")
    save: bool = Field(False, description="Save generated audio locally")


class AzureTTSRequest(BaseTTSRequest):
    """Azure-specific TTS request model"""

    engine: Literal[TTSEngine.AZURE] = TTSEngine.AZURE
    language: str = Field(..., description="Language code (e.g., en-US)")
    style: str = Field("default", description="Speaking style")
    rate: str = Field("0%", description="Speaking rate (-100% to 100%)")
    pitch: str = Field("0%", description="Voice pitch (-100% to 100%)")


class KokoroTTSRequest(BaseTTSRequest):
    """Kokoro-specific TTS request model"""

    engine: Literal[TTSEngine.KOKORO] = TTSEngine.KOKORO
    language: str = Field(..., description="Language code (e.g., en-US)")
    speed: float = Field(1.0, description="Speaking speed multiplier (0.5-2.0)")
    pitch: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Varispeed pitch multiplier (0.5-2.0). Pitch and tempo change together",
    )


class SesameTTSRequest(BaseTTSRequest):
    """Sesame-specific TTS request model"""

    engine: Literal[TTSEngine.SESAME] = TTSEngine.SESAME


# Union type for request validation
TTSRequest = AzureTTSRequest | KokoroTTSRequest | SesameTTSRequest


class EngineOptions(BaseModel):
    """Options for a specific TTS engine"""

    label: str
    voices: List[Dict[str, str]]
    languages: List[Dict[str, str]] = None  # Optional
    styles: List[Dict[str, str]] = None  # Optional


class TTSEngineOptions(BaseModel):
    """Response model for TTS options"""

    engines: Dict[str, EngineOptions]


# API Endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    status = {"status": "OK", "timestamp": datetime.now().isoformat(), "engines": []}

    # Check Azure
    if azure_speech_config:
        status["engines"].append("azure")

    # Check Kokoro
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{KOKORO_API_URL}/health", timeout=2.0)
            if response.status_code == 200:
                status["engines"].append("kokoro")
    except Exception:
        logger.exception(f"Unexpected error during Kokoro TTS health check")

    # Check Sesame
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SESAME_API_URL}/health", timeout=2.0)
            if response.status_code == 200:
                status["engines"].append("sesame")
    except Exception:
        logger.exception(f"Unexpected error during Sesame TTS health check")

    return status


@app.get("/options", response_model=TTSEngineOptions, summary="Get TTS options")
async def get_tts_options():
    """Get available TTS options for all engines including languages, voices, and styles"""

    languages = [
        {"value": "en-US", "label": "English (US)"},
        {"value": "en-GB", "label": "English (GB)"},
        {"value": "fr-FR", "label": "French (France)"},
        {"value": "es-ES", "label": "Spanish (Spain)"},
        {"value": "de-DE", "label": "German (Germany)"},
        {"value": "ja-JP", "label": "Japanese"},
        {"value": "ko-KR", "label": "Korean"},
        {"value": "zh-CN", "label": "Chinese (Simplified)"},
    ]
    styles = [
        {"value": "default", "label": "Default"},
        {"value": "cheerful", "label": "Cheerful"},
        {"value": "sad", "label": "Sad"},
        {"value": "angry", "label": "Angry"},
        {"value": "whispering", "label": "Whispering"},
    ]

    options = {
        "engines": {
            "azure": EngineOptions(
                label="Azure TTS",
                voices=[
                    {
                        "value": "en-US-AriaNeural",
                        "label": "Aria (en-US)",
                    },
                    {
                        "value": "en-US-GuyNeural",
                        "label": "Guy (en-US)",
                    },
                    {
                        "value": "en-US-NancyNeural",
                        "label": "Nancy (en-US)",
                    },
                    {
                        "value": "en-GB-MiaNeural",
                        "label": "Mia (en-GB)",
                    },
                    {
                        "value": "fr-FR-HenriNeural",
                        "label": "Henri (fr-FR)",
                    },
                    {
                        "value": "es-ES-ElviraNeural",
                        "label": "Elvira (es-ES)",
                    },
                    {
                        "value": "de-DE-KatjaNeural",
                        "label": "Katja (de-DE)",
                    },
                ],
                languages=languages,
                styles=styles,
            ),
            "kokoro": EngineOptions(
                label="Kokoro TTS",
                voices=[
                    # Kokoro voices - American Female (af_)
                    {"value": "af_alloy", "label": "Alloy (US Female)"},
                    {"value": "af_aoede", "label": "Aoede (US Female)"},
                    {"value": "af_bella", "label": "Bella (US Female)"},
                    {"value": "af_heart", "label": "Heart (US Female)"},
                    {"value": "af_jadzia", "label": "Jadzia (US Female)"},
                    {"value": "af_jessica", "label": "Jessica (US Female)"},
                    {"value": "af_kore", "label": "Kore (US Female)"},
                    {"value": "af_nicole", "label": "Nicole (US Female)"},
                    {"value": "af_nova", "label": "Nova (US Female)"},
                    {"value": "af_river", "label": "River (US Female)"},
                    {"value": "af_sarah", "label": "Sarah (US Female)"},
                    {"value": "af_sky", "label": "Sky (US Female)"},
                    {"value": "af_v0", "label": "V0 (US Female)"},
                    {
                        "value": "af_v0bella",
                        "label": "V0 Bella (US Female)",
                    },
                    {
                        "value": "af_v0irulan",
                        "label": "V0 Irulan (US Female)",
                    },
                    {
                        "value": "af_v0nicole",
                        "label": "V0 Nicole (US Female)",
                    },
                    {
                        "value": "af_v0sarah",
                        "label": "V0 Sarah (US Female)",
                    },
                    {"value": "af_v0sky", "label": "V0 Sky (US Female)"},
                    {
                        "value": "af_bella+af_sky",
                        "label": "Bella+Sky Mix (US Female)",
                    },
                    # Kokoro voices - American Male (am_)
                    {"value": "am_adam", "label": "Adam (US Male)"},
                    {"value": "am_echo", "label": "Echo (US Male)"},
                    {"value": "am_eric", "label": "Eric (US Male)"},
                    {"value": "am_fenrir", "label": "Fenrir (US Male)"},
                    {"value": "am_liam", "label": "Liam (US Male)"},
                    {"value": "am_michael", "label": "Michael (US Male)"},
                    {"value": "am_onyx", "label": "Onyx (US Male)"},
                    {"value": "am_puck", "label": "Puck (US Male)"},
                    {"value": "am_santa", "label": "Santa (US Male)"},
                    {"value": "am_v0adam", "label": "V0 Adam (US Male)"},
                    {
                        "value": "am_v0gurney",
                        "label": "V0 Gurney (US Male)",
                    },
                    {
                        "value": "am_v0michael",
                        "label": "V0 Michael (US Male)",
                    },
                    # Kokoro voices - British Female (bf_)
                    {"value": "bf_alice", "label": "Alice (UK Female)"},
                    {"value": "bf_emma", "label": "Emma (UK Female)"},
                    {"value": "bf_lily", "label": "Lily (UK Female)"},
                    {"value": "bf_v0emma", "label": "V0 Emma (UK Female)"},
                    {
                        "value": "bf_v0isabella",
                        "label": "V0 Isabella (UK Female)",
                    },
                    # Kokoro voices - British Male (bm_)
                    {"value": "bm_daniel", "label": "Daniel (UK Male)"},
                    {"value": "bm_fable", "label": "Fable (UK Male)"},
                    {"value": "bm_george", "label": "George (UK Male)"},
                    {"value": "bm_lewis", "label": "Lewis (UK Male)"},
                    {
                        "value": "bm_v0george",
                        "label": "V0 George (UK Male)",
                    },
                    {"value": "bm_v0lewis", "label": "V0 Lewis (UK Male)"},
                    # Kokoro voices - European Female (ef_)
                    {"value": "ef_dora", "label": "Dora (EU Female)"},
                    # Kokoro voices - European Male (em_)
                    {"value": "em_alex", "label": "Alex (EU Male)"},
                    {"value": "em_santa", "label": "Santa (EU Male)"},
                    # Kokoro voices - French Female (ff_)
                    {"value": "ff_siwis", "label": "Siwis (French Female)"},
                    # Kokoro voices - Hindi Female/Male (hf_/hm_)
                    {"value": "hf_alpha", "label": "Alpha (Hindi Female)"},
                    {"value": "hf_beta", "label": "Beta (Hindi Female)"},
                    {"value": "hm_omega", "label": "Omega (Hindi Male)"},
                    {"value": "hm_psi", "label": "Psi (Hindi Male)"},
                    # Kokoro voices - Italian Female/Male (if_/im_)
                    {"value": "if_sara", "label": "Sara (Italian Female)"},
                    {
                        "value": "im_nicola",
                        "label": "Nicola (Italian Male)",
                    },
                    # Kokoro voices - Japanese Female/Male (jf_/jm_)
                    {
                        "value": "jf_alpha",
                        "label": "Alpha (Japanese Female)",
                    },
                    {
                        "value": "jf_gongitsune",
                        "label": "Gongitsune (Japanese Female)",
                    },
                    {
                        "value": "jf_nezumi",
                        "label": "Nezumi (Japanese Female)",
                    },
                    {
                        "value": "jf_tebukuro",
                        "label": "Tebukuro (Japanese Female)",
                    },
                    {"value": "jm_kumo", "label": "Kumo (Japanese Male)"},
                    # Kokoro voices - Portuguese Female/Male (pf_/pm_)
                    {
                        "value": "pf_dora",
                        "label": "Dora (Portuguese Female)",
                    },
                    {"value": "pm_alex", "label": "Alex (Portuguese Male)"},
                    {
                        "value": "pm_santa",
                        "label": "Santa (Portuguese Male)",
                    },
                    # Kokoro voices - Chinese Female/Male (zf_/zm_)
                    {
                        "value": "zf_xiaobei",
                        "label": "Xiaobei (Chinese Female)",
                    },
                    {
                        "value": "zf_xiaoni",
                        "label": "Xiaoni (Chinese Female)",
                    },
                    {
                        "value": "zf_xiaoxiao",
                        "label": "Xiaoxiao (Chinese Female)",
                    },
                    {
                        "value": "zf_xiaoyi",
                        "label": "Xiaoyi (Chinese Female)",
                    },
                    {
                        "value": "zm_yunjian",
                        "label": "Yunjian (Chinese Male)",
                    },
                    {"value": "zm_yunxi", "label": "Yunxi (Chinese Male)"},
                    {
                        "value": "zm_yunxia",
                        "label": "Yunxia (Chinese Male)",
                    },
                    {
                        "value": "zm_yunyang",
                        "label": "Yunyang (Chinese Male)",
                    },
                ],
                languages=languages,
            ),
            "sesame": EngineOptions(
                label="Sesame TTS",
                voices=[{"value": "alloy", "label": "Alloy (Sesame)"}],
            ),
        }
    }
    return options


# TTS Engine Implementations
async def synthesize_with_azure(request: AzureTTSRequest) -> bytes:
    """
    Synthesize speech using Azure TTS

    Args:
        request: The Azure TTS request containing all parameters

    Returns:
        Audio data as bytes

    Raises:
        HTTPException: If synthesis fails
    """
    if not azure_speech_config:
        raise HTTPException(status_code=500, detail="Azure TTS not configured")

    try:
        # Configure the speech synthesizer
        azure_speech_config.speech_synthesis_voice_name = request.voice
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=azure_speech_config, audio_config=None
        )

        # Create SSML document
        ssml = f"""<speak xmlns="http://www.w3.org/2001/10/synthesis"
                xmlns:mstts="http://www.w3.org/2001/mstts"
                xmlns:emo="http://www.w3.org/2009/10/emotionml"
                version="1.0" xml:lang="{request.language}">
                <voice name="{request.voice}">
                    <s/>
                    <mstts:express-as style="{request.style}">
                        <prosody rate="{request.rate}" pitch="{request.pitch}">
                            {request.text}
                        </prosody>
                    </mstts:express-as>
                    <s/>
                </voice>
            </speak>"""

        # Synthesize speech
        speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()

        # Process result
        if (
            speech_synthesis_result.reason
            == speechsdk.ResultReason.SynthesizingAudioCompleted
        ):
            logger.info(f"Azure speech synthesized for text: {request.text[:50]}...")
            return speech_synthesis_result.audio_data

        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            logger.warning(
                f"Azure speech synthesis canceled: {cancellation_details.reason}"
            )

            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logger.error(
                        f"Azure Speech SDK error: {cancellation_details.error_details}"
                    )
            raise HTTPException(
                status_code=500,
                detail=f"Azure speech synthesis canceled: {cancellation_details.reason}",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected error during Azure speech synthesis",
            )

    except Exception:
        logger.error("Unexpected error synthesizing speech with Azure TTS")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error synthesizing speech with Azure TTS",
        )


def apply_varispeed_pitch(wav: bytes, pitch: float) -> bytes:
    """
    Shift pitch and tempo together by scaling the sample rate declared in a WAV header.

    The samples stay untouched: a player (or a resampler such as ffmpeg) reads them at
    the new rate, so 24 kHz audio declared as 28.8 kHz plays 1.2x higher and faster.

    Args:
        wav: A RIFF/WAVE file
        pitch: Factor to scale the sample rate by

    Returns:
        The WAV with its `fmt ` chunk's sample rate and byte rate scaled
    """
    if pitch == 1.0:
        return wav
    if wav[0:4] != b"RIFF" or wav[8:12] != b"WAVE":
        raise ValueError("Kokoro did not return a RIFF/WAVE file")

    out = bytearray(wav)
    pos = 12
    # Walk the chunks up to `fmt ` (normally the first one). Chunks after it, like
    # `data`, are never parsed, so placeholder sizes from a streaming writer are fine
    while pos + 8 <= len(out):
        chunk_id = bytes(out[pos : pos + 4])
        (chunk_size,) = struct.unpack_from("<I", out, pos + 4)
        if chunk_id == b"fmt ":
            (sample_rate,) = struct.unpack_from("<I", out, pos + 12)
            (block_align,) = struct.unpack_from("<H", out, pos + 20)
            new_rate = round(sample_rate * pitch)
            struct.pack_into("<I", out, pos + 12, new_rate)
            struct.pack_into("<I", out, pos + 16, new_rate * block_align)
            return bytes(out)
        pos += 8 + chunk_size + (chunk_size & 1)

    raise ValueError("Kokoro's WAV has no fmt chunk")


async def synthesize_with_kokoro(request: KokoroTTSRequest) -> bytes:
    """
    Synthesize speech using Kokoro TTS

    Args:
        request: The Kokoro TTS request containing all parameters

    Returns:
        Audio data as bytes

    Raises:
        HTTPException: If synthesis fails
    """
    try:
        # Kokoro-FastAPI has no pitch option, so pitch is applied to its WAV afterwards.
        # stream=False makes it return one complete WAV instead of streamed chunks
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KOKORO_API_URL}/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": request.text.replace("\n", ". "),
                    "voice": request.voice,
                    "language": request.language,
                    "response_format": "wav",
                    "speed": request.speed,
                    "stream": False,
                },
            )

            response.raise_for_status()
            logger.info(f"Kokoro speech synthesized for text: {request.text[:50]}...")
            return apply_varispeed_pitch(response.content, request.pitch)

    except httpx.HTTPStatusError as e:
        logger.error(f"Kokoro API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Kokoro API error: {e.response.text}",
        )
    except Exception:
        logger.error("Unexpected error synthesizing speech with Kokoro TTS")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error synthesizing speech with Kokoro TTS",
        )


async def synthesize_with_sesame(request: SesameTTSRequest) -> bytes:
    """
    Synthesize speech using Sesame TTS

    Args:
        request: The Sesame TTS request containing all parameters

    Returns:
        Audio data as bytes

    Raises:
        HTTPException: If synthesis fails
    """
    try:
        # Call Sesame API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SESAME_API_URL}/v1/audio/speech",
                json={
                    "model": "csm-1b",
                    "input": request.text,
                    "voice": request.voice,
                    "response_format": "wav",
                },
                timeout=60.0,
            )

            response.raise_for_status()
            logger.info(f"Sesame speech synthesized for text: {request.text[:50]}...")
            return response.content

    except httpx.HTTPStatusError as e:
        logger.error(f"Sesame API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Sesame API error: {e.response.text}",
        )
    except Exception:
        logger.error("Unexpected error synthesizing speech with Sesame TTS")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error synthesizing speech with Sesame TTS",
        )


@app.post("/generate", summary="Generate speech from text")
async def generate_endpoint(request: TTSRequest = Body(...)):
    """
    Generate speech from text using the specified engine

    Args:
        request: The TTS request containing engine selection and parameters

    Returns:
        Audio data as WAV file

    Raises:
        HTTPException: If synthesis fails or engine is not supported
    """
    logger.info(f"TTS request received for {request.engine}")

    try:
        # Route to appropriate engine based on request type
        if isinstance(request, AzureTTSRequest):
            audio_data = await synthesize_with_azure(request)
        elif isinstance(request, KokoroTTSRequest):
            audio_data = await synthesize_with_kokoro(request)
        elif isinstance(request, SesameTTSRequest):
            audio_data = await synthesize_with_sesame(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported TTS engine")

        # Save audio data to disk
        if request.save:
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{request.engine}_{request.voice}_{timestamp}.wav"
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "wb") as f:
                f.write(audio_data)
            logger.info(f"Saved audio file to {file_path}")

        # Return audio data
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_{request.engine}.wav"
            },
        )

    except Exception:
        logger.exception("Unexpected error during speech synthesis")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during speech synthesis",
        )
