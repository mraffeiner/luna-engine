from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


app = FastAPI()

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class LLMRequest(BaseModel):
    model: str
    prompt: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/chat")
async def chat_endpoint(request: LLMRequest = Body()):
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
                    logging.info(f"Chunk: {content}")
                    yield content
            logging.info("Stream finished")
        except openai.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get response from OpenAI API"
            )
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    return StreamingResponse(stream_response(), media_type="text/event-stream")
