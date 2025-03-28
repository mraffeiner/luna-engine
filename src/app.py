from contextlib import asynccontextmanager
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import openai
from openai import OpenAI
import os
import httpx
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

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
    title="LLM Service API",
    description="LLM service using OpenAI, Groq, and local models to generate responses",
    lifespan=lifespan,
)

load_dotenv()

# OpenAI configuration
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Groq configuration
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL"),
)

# Google configuration
google_client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url=os.getenv("GOOGLE_BASE_URL"),
)

# Local LLM configuration
local_client = OpenAI(base_url=os.getenv("LOCAL_BASE_URL"))

# Local models
LOCAL_MODELS = [
    {
        "provider": "local",
        "id": "llama-3.2-3b-instruct-uncensored",
        "name": "Llama 3.2 3B Instruct Uncensored",
        "isReasoning": False,
    },
    {
        "provider": "local",
        "id": "llama-exaone-deep-7.8b",
        "name": "EXAONE Deep 7.8B",
        "isReasoning": True,
    },
]


# OpenAI models
OPENAI_MODELS = [
    {
        "provider": "openai",
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "isReasoning": False,
    }
]

# Groq models
GROQ_MODELS = [
    {
        "provider": "groq",
        "id": "deepseek-r1-distill-llama-70b",
        "name": "DeepSeek R1 Llama 70B",
        "isReasoning": True,
    },
    {
        "provider": "groq",
        "id": "qwen-qwq-32b",
        "name": "Qwen QwQ 32B",
        "isReasoning": True,
    },
]

# Google models
GOOGLE_MODELS = [
    {
        "provider": "google",
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "isReasoning": False,
    }
]


async def is_local_llm_available():
    """Check if the local LLM endpoint is available."""
    try:
        logger.info(
            f"Checking local LLM availability at {local_client.base_url}/models"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{local_client.base_url}/models", timeout=3.0)
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
    except Exception:
        logger.exception("Unexpected error when checking for local LLM")
        return False


class LLMRequest(BaseModel):
    provider: str
    model: str
    system_prompt: str
    prompt: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/models")
async def get_models():
    available_models = []

    # Add OpenAI models if API key is available
    if openai_client.api_key:
        logger.info("OpenAI API key is available, adding OpenAI models")
        for model in OPENAI_MODELS:
            available_models.append(model)
            logger.info(f"Added {model['id']} by {model['provider']}")
    else:
        logger.warning("OpenAI API key is not available, skipping OpenAI models")

    # Add Groq models if API key is available
    if groq_client.api_key:
        logger.info("Groq API key is available, adding Groq models")
        for model in GROQ_MODELS:
            available_models.append(model)
            logger.info(f"Added {model['id']} by {model['provider']}")
    else:
        logger.warning("Groq API key is not available, skipping Groq models")

    # Add Google models if API key is available
    if google_client.api_key:
        logger.info("Google API key is available, adding Google models")
        for model in GOOGLE_MODELS:
            available_models.append(model)
            logger.info(f"Added {model['id']} by {model['provider']}")
    else:
        logger.warning("Google API key is not available, skipping Google models")

    # Add local models if endpoint is available
    local_available = await is_local_llm_available()
    if local_available:
        logger.info("Local LLM is available, adding local models")
        for model in LOCAL_MODELS:
            available_models.append(model)
            logger.info(f"Added {model['id']} by {model['provider']}")
    else:
        logger.warning("Local LLM is not available, skipping local models")

    logger.info(f"Returning {len(available_models)} available models")
    return JSONResponse(content=available_models)


async def stream_from_openai_compatible(
    provider: str, model: str, system_prompt: str = "", prompt: str = ""
):
    """Stream response from OpenAI API compatible LLM."""
    try:
        if provider == "openai":
            client = openai_client
            logger.info(f"Using OpenAI API with model {model}")
        elif provider == "groq":
            client = groq_client
            logger.info(f"Using Groq API with model {model}")
        elif provider == "google":
            client = google_client
            logger.info(f"Using Google API with model {model}")
        elif provider == "local":
            client = local_client
            logger.info(f"Using Local LLM API with model {model}")
        else:
            logger.error(f"Incompatible provider [{provider}] for model [{model}]")
            raise HTTPException(
                status_code=400,
                detail=f"Incompatible provider [{provider}] for model [{model}]",
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
        logger.info("Stream finished")
    except openai.APIError:
        logger.exception("OpenAI API error")
        raise HTTPException(
            status_code=500, detail="Failed to get response from OpenAI API"
        )
    except Exception:
        logger.exception("Unexpected error during LLM response generation")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error during LLM response generation",
        )


@app.post("/generate")
async def generate_endpoint(request: LLMRequest = Body()):
    async def stream_response():
        if request.provider in ["openai", "groq", "google", "local"]:
            logger.info(
                f"Generating response for model {request.model} by {request.provider} using OpenAI API client"
            )
            fullContent = ""
            async for content in stream_from_openai_compatible(
                request.provider, request.model, request.system_prompt, request.prompt
            ):
                fullContent += content
                yield content
            logger.info(f"Finished response: {fullContent}")
        else:
            logger.error(f"Unknown provider: {request.provider}")
            raise HTTPException(
                status_code=400, detail=f"Unknown provider: {request.provider}"
            )

    return StreamingResponse(stream_response(), media_type="text/event-stream")
