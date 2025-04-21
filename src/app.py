import asyncio
import os
import httpx
import logging
from datetime import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI, OpenAIError, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure uvicorn access logger to match our format
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
    description="LLM service using OpenAI, Groq, Google, and local models to generate responses",
    lifespan=lifespan,
)

load_dotenv()

# --- Client Configurations ---
# Use AsyncOpenAI for non-blocking API calls
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL"),
)
google_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url=os.getenv("GOOGLE_BASE_URL"),
)
local_client = AsyncOpenAI(
    base_url=os.getenv("LOCAL_BASE_URL", "http://host.docker.internal:1234/v1")
)  # Default added


async def is_local_llm_available():
    """Check if the local LLM endpoint is available using a quick HEAD request."""
    local_base_url = str(local_client.base_url)  # Ensure it's a string
    if not local_base_url:
        logger.warning("Local LLM base URL is not configured.")
        return False
    try:
        logger.info(f"Checking local LLM availability at {local_base_url}")
        async with httpx.AsyncClient() as client:
            # Use HEAD request for efficiency, target base URL or /health if available
            response = await client.head(local_base_url, timeout=3.0)
            # Consider status code 405 (Method Not Allowed) as OK if HEAD isn't supported
            if 200 <= response.status_code < 300 or response.status_code == 405:
                logger.info(f"Local LLM is available (Status: {response.status_code})")
                return True
            else:
                logger.warning(
                    f"Local LLM check returned non-success status: {response.status_code}"
                )
                return False
    except (httpx.TimeoutException, httpx.ConnectError):
        logger.warning(f"Could not connect to Local LLM at {local_base_url}")
        return False
    except Exception:
        logger.exception(f"Unexpected error checking local LLM at {local_base_url}")
        return False


async def fetch_models_from_provider(client: AsyncOpenAI, provider_name: str):
    """Fetches models from an OpenAI-compatible API and adds provider info."""
    models = []
    try:
        logger.info(f"Fetching models from {provider_name}...")
        model_list_response = await client.models.list()
        for model in model_list_response.data:
            # Add provider information required by the frontend
            models.append(
                {"provider": provider_name, "id": model.id, "name": model.id}
            )  # Use ID as name for now
        logger.info(f"Successfully fetched {len(models)} models from {provider_name}")
    except AuthenticationError:
        logger.warning(f"Authentication error with {provider_name} API. Check API key.")
    except APIConnectionError:
        logger.warning(
            f"Could not connect to {provider_name} API at {client.base_url}."
        )
    except OpenAIError as e:
        logger.warning(f"API error fetching models from {provider_name}: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error fetching models from {provider_name}")
    return models


class LLMRequest(BaseModel):
    provider: str
    model: str
    system_prompt: str
    prompt: str


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


@app.get("/models")
async def get_models():
    """Dynamically fetches available models from all configured providers."""
    tasks = []
    provider_clients = {
        "openai": openai_client,
        "groq": groq_client,
        "google": google_client,
    }

    for provider, client in provider_clients.items():
        # Check if API key exists (for hosted providers) or base_url is set
        if client.api_key or (
            provider == "google" and client.base_url
        ):  # Google uses base_url + key
            logger.info(
                f"{provider.capitalize()} client configured, scheduling model fetch."
            )
            tasks.append(fetch_models_from_provider(client, provider))
        else:
            logger.warning(f"{provider.capitalize()} client not configured, skipping.")

    # Fetch models from cloud providers concurrently
    results = await asyncio.gather(*tasks)
    available_models = [
        model for sublist in results for model in sublist
    ]  # Flatten list

    # Check and fetch local models separately
    if await is_local_llm_available():
        logger.info("Local LLM available, fetching models.")
        local_models = await fetch_models_from_provider(local_client, "local")
        available_models.extend(local_models)
    else:
        logger.warning("Local LLM not available, skipping local models.")

    logger.info(f"Returning {len(available_models)} available models.")

    return JSONResponse(content=available_models)


async def stream_from_openai_compatible(
    provider: str, model: str, system_prompt: str = "", prompt: str = ""
):
    """Stream response from an OpenAI API compatible LLM using AsyncClient."""
    try:
        client_map = {
            "openai": openai_client,
            "groq": groq_client,
            "google": google_client,
            "local": local_client,
        }
        client = client_map.get(provider)

        if not client:
            logger.error(f"Invalid provider specified: {provider}")
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

        # Check configuration again before making the call
        if provider != "local" and not client.api_key:
            logger.error(f"API key for provider {provider} is missing.")
            raise HTTPException(
                status_code=500, detail=f"API key for {provider} not configured."
            )
        if provider == "local" and not str(client.base_url):
            logger.error("Local LLM base URL is not configured.")
            raise HTTPException(status_code=500, detail="Local LLM URL not configured.")

        logger.info(f"Streaming from {provider} using model {model}")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        # Use async for to iterate over the async stream
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
        logger.info(f"Stream finished for {provider} model {model}")

    except AuthenticationError:
        logger.error(f"Authentication failed for {provider}. Check API Key.")
        raise HTTPException(
            status_code=401, detail=f"Authentication failed for {provider}."
        )
    except APIConnectionError:
        logger.error(f"Could not connect to {provider} API at {client.base_url}.")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {provider}.")
    except OpenAIError as e:
        logger.exception(f"{provider} API error")
        raise HTTPException(
            status_code=getattr(e, "status_code", 500),
            detail=(
                f"Failed to get response from {provider} API: {e.message}"
                if hasattr(e, "message")
                else str(e)
            ),
        )
    except Exception:
        logger.exception(f"Unexpected error during {provider} stream")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during {provider} response generation",
        )


@app.post("/generate")
async def generate_endpoint(request: LLMRequest = Body()):
    """Endpoint to generate text based on provider, model, and prompts."""
    logger.info(
        f"Received generation request for model {request.model} via {request.provider}"
    )

    async def stream_response():
        full_content = ""
        try:
            async for content in stream_from_openai_compatible(
                request.provider, request.model, request.system_prompt, request.prompt
            ):
                full_content += content
                yield content
            logger.info(
                f"Finished streaming response for {request.provider}/{request.model}. Total length: {len(full_content)}"
            )
        except HTTPException as http_exc:
            # Log the error but let FastAPI handle the response based on the raised HTTPException
            logger.error(
                f"HTTPException during streaming for {request.provider}/{request.model}: {http_exc.detail}"
            )
            raise http_exc
        except Exception:
            logger.exception(
                f"Unhandled exception during streaming for {request.provider}/{request.model}"
            )
            # Yielding an error message might be better for streaming UX
            yield f"Error: An unexpected error occurred."

    return StreamingResponse(stream_response(), media_type="text/event-stream")
