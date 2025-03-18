from contextlib import asynccontextmanager
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
import httpx
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
    title="LLM Service API",
    description="LLM service using OpenAI's models to generate responses",
    lifespan=lifespan,
)

load_dotenv()

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

# Local LLM configuration
LOCAL_API_BASE_URL = os.getenv(
    "LOCAL_API_BASE_URL", "http://host.docker.internal:1234/v1"
)


# Local models
LOCAL_MODELS = {"llama-3.2-3b-instruct-uncensored": "Llama 3.2 3B Instruct Uncensored"}

# OpenAI models
OPENAI_MODELS = {"gpt-4o-mini": "GPT-4o Mini"}


async def is_local_llm_available():
    """Check if the local LLM endpoint is available."""
    if not LOCAL_API_BASE_URL:
        logger.warning("LOCAL_API_BASE_URL is not set")
        return False

    try:
        logger.info(f"Checking local LLM availability at {LOCAL_API_BASE_URL}/models")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LOCAL_API_BASE_URL}/models", timeout=3.0)
            if response.status_code == 200:
                logger.info("Local LLM is available")
                return True
            else:
                logger.warning(
                    f"Local LLM returned non-200 status: {response.status_code}"
                )
                return False
    except httpx.TimeoutException:
        logger.warning("Local LLM connection timed out")
        return False
    except httpx.ConnectError:
        logger.warning("Could not connect to Local LLM")
        return False
    except Exception as e:
        logger.warning(f"Local LLM not available: {str(e)}")
        return False


class LLMRequest(BaseModel):
    model: str
    prompt: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/models")
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

    # Add local models if endpoint is available
    local_available = await is_local_llm_available()
    if local_available:
        logger.info("Local LLM is available, adding local models")
        for model_id, model_name in LOCAL_MODELS.items():
            available_models.append({"value": model_id, "label": model_name})
            logger.info(f"Added local model: {model_id} ({model_name})")
    else:
        logger.warning("Local LLM is not available, skipping local models")

    logger.info(f"Returning {len(available_models)} available models")
    return JSONResponse(content={"models": available_models})


async def stream_from_openai(model: str, prompt: str):
    """Stream response from OpenAI API."""
    try:
        logger.info(f"Using OpenAI API with model {model}")
        stream = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
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
    except Exception as e:
        logger.exception(
            f"Unexpected error during OpenAI response generation: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during OpenAI response generation: {str(e)}",
        )


async def stream_from_local_llm(model: str, prompt: str):
    """Stream response from local LLM API."""
    try:
        logger.info(f"Using Local LLM API with model {model}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LOCAL_API_BASE_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                },
                headers={"Content-Type": "application/json"},
                timeout=60.0,
            )

            if response.status_code != 200:
                logger.error(
                    f"Local LLM API error: {response.status_code} {response.text}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get response from Local LLM API: {response.status_code}",
                )

            # Process the streaming response
            async for line in response.aiter_lines():
                line = line.strip()
                if line and line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = line[6:]  # Remove "data: " prefix
                        if data:
                            import json

                            chunk = json.loads(data)
                            content = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if content:
                                logger.info(f"Local LLM chunk: {content}")
                                yield content
                    except Exception as e:
                        logger.exception(f"Error parsing chunk: {line}")
                        continue

            logger.info("Local LLM stream finished")
    except httpx.HTTPError as e:
        logger.exception(f"HTTP error with Local LLM: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"HTTP error with Local LLM: {str(e)}"
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error during Local LLM response generation: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during Local LLM response generation: {str(e)}",
        )


@app.post("/generate")
async def generate_endpoint(request: LLMRequest = Body()):
    async def stream_response():
        # Determine source based on model
        if request.model in OPENAI_MODELS:
            async for content in stream_from_openai(request.model, request.prompt):
                yield content
        elif request.model in LOCAL_MODELS:
            async for content in stream_from_local_llm(request.model, request.prompt):
                yield content
        else:
            logger.error(f"Unknown model: {request.model}")
            raise HTTPException(
                status_code=400, detail=f"Unknown model: {request.model}"
            )

    return StreamingResponse(stream_response(), media_type="text/event-stream")
