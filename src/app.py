from fastapi import FastAPI, Body, Response
from pydantic import BaseModel
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


app = FastAPI()

load_dotenv()

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SUBSCRIPTION"), endpoint=os.getenv("AZURE_ENDPOINT")
)
speech_config.set_speech_synthesis_output_format(
    speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm
)


class TTSRequest(BaseModel):
    language: str
    voice: str
    style: str
    rate: str
    pitch: str
    text: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/tts")
async def tts_endpoint(request: TTSRequest = Body()):
    speech_config.speech_synthesis_voice_name = request.voice
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )
    speech_synthesis_result = speech_synthesizer.speak_ssml_async(
        f"""<speak xmlns="http://www.w3.org/2001/10/synthesis"
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
    ).get()
    if (
        speech_synthesis_result.reason
        == speechsdk.ResultReason.SynthesizingAudioCompleted
    ):
        logging.info(f"Speech synthesized for text {request.text}")
        return Response(
            content=speech_synthesis_result.audio_data, media_type="audio/wav"
        )
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        logging.warning(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                logging.error(
                    f"Azure Speech SDK error: {cancellation_details.error_details}"
                )
        raise HTTPException(status_code=500, detail="Speech synthesis canceled")
    else:
        raise HTTPException(
            status_code=500,
            detail="Unexpected error during speech synthesis",
        )
