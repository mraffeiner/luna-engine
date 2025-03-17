from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)


app = FastAPI()

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class LLMRequest(BaseModel):
    model: str
    prompt: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/models")
async def get_models():
    return JSONResponse(
        content={
            "models": [
                {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
                {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
            ]
        }
    )


@app.post("/generate")
async def generate_endpoint(request: LLMRequest = Body()):
    async def stream_response():
        try:
            stream = openai.chat.completions.create(
                model=request.model,
                messages=[{"role": "user", "content": request.prompt}],
                stream=True,
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    logger.info(f"Chunk: {content}")
                    yield content
            logger.info("Stream finished")
        except openai.APIError:
            logger.exception("OpenAI API error")
            raise HTTPException(
                status_code=500, detail="Failed to get response from OpenAI API"
            )
        except Exception:
            logger.exception("Unexpected error during response generation")
            raise HTTPException(
                status_code=500, detail="Unexpected error during response generation"
            )

    return StreamingResponse(stream_response(), media_type="text/event-stream")
