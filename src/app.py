from fastapi import FastAPI, Body, Response, HTTPException
from pydantic import BaseModel, Field
import azure.cognitiveservices.speech as speechsdk
import os
import httpx
from dotenv import load_dotenv
import logging
from enum import Enum
from typing import List, Dict, Literal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TTS Service API",
    description="Text-to-Speech service supporting multiple engines",
)

# Load environment variables
load_dotenv()


# TTS Engine configuration
class TTSEngine(str, Enum):
    """Supported TTS engines"""

    AZURE = "azure"
    KOKORO = "kokoro"


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


# API Models
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


class TTSEngineOptions(BaseModel):
    """Response model for TTS options"""

    engines: List[Dict[str, str]]
    languages: List[Dict[str, str]]
    voices: List[Dict[str, str]]
    styles: List[Dict[str, str]]


# API Endpoints
@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Check the health of the TTS service and available engines"""
    status = {"status": "ok", "engines": []}

    # Check Azure
    if azure_speech_config:
        status["engines"].append("azure")

    # Check Kokoro
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{KOKORO_API_URL}/health", timeout=2.0)
            if response.status_code == 200:
                status["engines"].append("kokoro")
    except Exception as e:
        logger.warning(f"Kokoro health check failed: {e}")

    return status


@app.get("/options", response_model=TTSEngineOptions, summary="Get TTS options")
async def get_tts_options():
    """Get available TTS options for all engines including languages, voices, and styles"""
    return {
        "engines": [
            {"value": "azure", "label": "Azure TTS"},
            {"value": "kokoro", "label": "Kokoro TTS"},
        ],
        "languages": [
            {"value": "en-US", "label": "English (US)"},
            {"value": "en-GB", "label": "English (GB)"},
            {"value": "fr-FR", "label": "French (France)"},
            {"value": "es-ES", "label": "Spanish (Spain)"},
            {"value": "de-DE", "label": "German (Germany)"},
            {"value": "ja-JP", "label": "Japanese"},
            {"value": "ko-KR", "label": "Korean"},
            {"value": "zh-CN", "label": "Chinese (Simplified)"},
        ],
        "voices": [
            # Azure voices
            {"value": "en-US-AriaNeural", "label": "Aria (en-US)", "engine": "azure"},
            {"value": "en-US-GuyNeural", "label": "Guy (en-US)", "engine": "azure"},
            {"value": "en-US-NancyNeural", "label": "Nancy (en-US)", "engine": "azure"},
            {"value": "en-GB-MiaNeural", "label": "Mia (en-GB)", "engine": "azure"},
            {"value": "fr-FR-HenriNeural", "label": "Henri (fr-FR)", "engine": "azure"},
            {
                "value": "es-ES-ElviraNeural",
                "label": "Elvira (es-ES)",
                "engine": "azure",
            },
            {"value": "de-DE-KatjaNeural", "label": "Katja (de-DE)", "engine": "azure"},
            # Kokoro voices - American Female (af_)
            {"value": "af_alloy", "label": "Alloy (US Female)", "engine": "kokoro"},
            {"value": "af_aoede", "label": "Aoede (US Female)", "engine": "kokoro"},
            {"value": "af_bella", "label": "Bella (US Female)", "engine": "kokoro"},
            {"value": "af_heart", "label": "Heart (US Female)", "engine": "kokoro"},
            {"value": "af_jadzia", "label": "Jadzia (US Female)", "engine": "kokoro"},
            {"value": "af_jessica", "label": "Jessica (US Female)", "engine": "kokoro"},
            {"value": "af_kore", "label": "Kore (US Female)", "engine": "kokoro"},
            {"value": "af_nicole", "label": "Nicole (US Female)", "engine": "kokoro"},
            {"value": "af_nova", "label": "Nova (US Female)", "engine": "kokoro"},
            {"value": "af_river", "label": "River (US Female)", "engine": "kokoro"},
            {"value": "af_sarah", "label": "Sarah (US Female)", "engine": "kokoro"},
            {"value": "af_sky", "label": "Sky (US Female)", "engine": "kokoro"},
            {"value": "af_v0", "label": "V0 (US Female)", "engine": "kokoro"},
            {
                "value": "af_v0bella",
                "label": "V0 Bella (US Female)",
                "engine": "kokoro",
            },
            {
                "value": "af_v0irulan",
                "label": "V0 Irulan (US Female)",
                "engine": "kokoro",
            },
            {
                "value": "af_v0nicole",
                "label": "V0 Nicole (US Female)",
                "engine": "kokoro",
            },
            {
                "value": "af_v0sarah",
                "label": "V0 Sarah (US Female)",
                "engine": "kokoro",
            },
            {"value": "af_v0sky", "label": "V0 Sky (US Female)", "engine": "kokoro"},
            {
                "value": "af_bella+af_sky",
                "label": "Bella+Sky Mix (US Female)",
                "engine": "kokoro",
            },
            # Kokoro voices - American Male (am_)
            {"value": "am_adam", "label": "Adam (US Male)", "engine": "kokoro"},
            {"value": "am_echo", "label": "Echo (US Male)", "engine": "kokoro"},
            {"value": "am_eric", "label": "Eric (US Male)", "engine": "kokoro"},
            {"value": "am_fenrir", "label": "Fenrir (US Male)", "engine": "kokoro"},
            {"value": "am_liam", "label": "Liam (US Male)", "engine": "kokoro"},
            {"value": "am_michael", "label": "Michael (US Male)", "engine": "kokoro"},
            {"value": "am_onyx", "label": "Onyx (US Male)", "engine": "kokoro"},
            {"value": "am_puck", "label": "Puck (US Male)", "engine": "kokoro"},
            {"value": "am_santa", "label": "Santa (US Male)", "engine": "kokoro"},
            {"value": "am_v0adam", "label": "V0 Adam (US Male)", "engine": "kokoro"},
            {
                "value": "am_v0gurney",
                "label": "V0 Gurney (US Male)",
                "engine": "kokoro",
            },
            {
                "value": "am_v0michael",
                "label": "V0 Michael (US Male)",
                "engine": "kokoro",
            },
            # Kokoro voices - British Female (bf_)
            {"value": "bf_alice", "label": "Alice (UK Female)", "engine": "kokoro"},
            {"value": "bf_emma", "label": "Emma (UK Female)", "engine": "kokoro"},
            {"value": "bf_lily", "label": "Lily (UK Female)", "engine": "kokoro"},
            {"value": "bf_v0emma", "label": "V0 Emma (UK Female)", "engine": "kokoro"},
            {
                "value": "bf_v0isabella",
                "label": "V0 Isabella (UK Female)",
                "engine": "kokoro",
            },
            # Kokoro voices - British Male (bm_)
            {"value": "bm_daniel", "label": "Daniel (UK Male)", "engine": "kokoro"},
            {"value": "bm_fable", "label": "Fable (UK Male)", "engine": "kokoro"},
            {"value": "bm_george", "label": "George (UK Male)", "engine": "kokoro"},
            {"value": "bm_lewis", "label": "Lewis (UK Male)", "engine": "kokoro"},
            {
                "value": "bm_v0george",
                "label": "V0 George (UK Male)",
                "engine": "kokoro",
            },
            {"value": "bm_v0lewis", "label": "V0 Lewis (UK Male)", "engine": "kokoro"},
            # Kokoro voices - European Female (ef_)
            {"value": "ef_dora", "label": "Dora (EU Female)", "engine": "kokoro"},
            # Kokoro voices - European Male (em_)
            {"value": "em_alex", "label": "Alex (EU Male)", "engine": "kokoro"},
            {"value": "em_santa", "label": "Santa (EU Male)", "engine": "kokoro"},
            # Kokoro voices - French Female (ff_)
            {"value": "ff_siwis", "label": "Siwis (French Female)", "engine": "kokoro"},
            # Kokoro voices - Hindi Female/Male (hf_/hm_)
            {"value": "hf_alpha", "label": "Alpha (Hindi Female)", "engine": "kokoro"},
            {"value": "hf_beta", "label": "Beta (Hindi Female)", "engine": "kokoro"},
            {"value": "hm_omega", "label": "Omega (Hindi Male)", "engine": "kokoro"},
            {"value": "hm_psi", "label": "Psi (Hindi Male)", "engine": "kokoro"},
            # Kokoro voices - Italian Female/Male (if_/im_)
            {"value": "if_sara", "label": "Sara (Italian Female)", "engine": "kokoro"},
            {
                "value": "im_nicola",
                "label": "Nicola (Italian Male)",
                "engine": "kokoro",
            },
            # Kokoro voices - Japanese Female/Male (jf_/jm_)
            {
                "value": "jf_alpha",
                "label": "Alpha (Japanese Female)",
                "engine": "kokoro",
            },
            {
                "value": "jf_gongitsune",
                "label": "Gongitsune (Japanese Female)",
                "engine": "kokoro",
            },
            {
                "value": "jf_nezumi",
                "label": "Nezumi (Japanese Female)",
                "engine": "kokoro",
            },
            {
                "value": "jf_tebukuro",
                "label": "Tebukuro (Japanese Female)",
                "engine": "kokoro",
            },
            {"value": "jm_kumo", "label": "Kumo (Japanese Male)", "engine": "kokoro"},
            # Kokoro voices - Portuguese Female/Male (pf_/pm_)
            {
                "value": "pf_dora",
                "label": "Dora (Portuguese Female)",
                "engine": "kokoro",
            },
            {"value": "pm_alex", "label": "Alex (Portuguese Male)", "engine": "kokoro"},
            {
                "value": "pm_santa",
                "label": "Santa (Portuguese Male)",
                "engine": "kokoro",
            },
            # Kokoro voices - Chinese Female/Male (zf_/zm_)
            {
                "value": "zf_xiaobei",
                "label": "Xiaobei (Chinese Female)",
                "engine": "kokoro",
            },
            {
                "value": "zf_xiaoni",
                "label": "Xiaoni (Chinese Female)",
                "engine": "kokoro",
            },
            {
                "value": "zf_xiaoxiao",
                "label": "Xiaoxiao (Chinese Female)",
                "engine": "kokoro",
            },
            {
                "value": "zf_xiaoyi",
                "label": "Xiaoyi (Chinese Female)",
                "engine": "kokoro",
            },
            {
                "value": "zm_yunjian",
                "label": "Yunjian (Chinese Male)",
                "engine": "kokoro",
            },
            {"value": "zm_yunxi", "label": "Yunxi (Chinese Male)", "engine": "kokoro"},
            {
                "value": "zm_yunxia",
                "label": "Yunxia (Chinese Male)",
                "engine": "kokoro",
            },
            {
                "value": "zm_yunyang",
                "label": "Yunyang (Chinese Male)",
                "engine": "kokoro",
            },
        ],
        "styles": [
            {"value": "default", "label": "Default"},
            {"value": "cheerful", "label": "Cheerful"},
            {"value": "sad", "label": "Sad"},
            {"value": "angry", "label": "Angry"},
            {"value": "whispering", "label": "Whispering"},
        ],
    }


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

    except Exception as e:
        logger.error(f"Error with Azure TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error with Azure TTS: {str(e)}")


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
        # Call Kokoro API with direct speed parameter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KOKORO_API_URL}/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": request.text.replace("\n", ". "),
                    "voice": request.voice,
                    "language": request.language,
                    "voice": request.voice,
                    "response_format": "wav",
                    "speed": request.speed,
                    "pitch": request.pitch,
                },
                timeout=30.0,
            )

            response.raise_for_status()
            logger.info(f"Kokoro speech synthesized for text: {request.text[:50]}...")
            return response.content

    except httpx.HTTPStatusError as e:
        logger.error(f"Kokoro API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Kokoro API error: {e.response.text}",
        )
    except Exception as e:
        logger.error(f"Error with Kokoro TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error with Kokoro TTS: {str(e)}")


@app.post("/tts", summary="Generate speech from text")
async def tts_endpoint(request: TTSRequest = Body(...)):
    """
    Generate speech from text using the specified engine

    Args:
        request: The TTS request containing engine selection and parameters

    Returns:
        Audio data as WAV file

    Raises:
        HTTPException: If synthesis fails or engine is not supported
    """
    logger.info(f"TTS request received for engine: {request.engine}")

    try:
        # Route to appropriate engine based on request type
        if isinstance(request, AzureTTSRequest):
            audio_data = await synthesize_with_azure(request)
        elif isinstance(request, KokoroTTSRequest):
            audio_data = await synthesize_with_kokoro(request)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported TTS engine: {request.engine}"
            )

        # Return audio data
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_{request.engine}.wav"
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in TTS endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during speech synthesis: {str(e)}",
        )
