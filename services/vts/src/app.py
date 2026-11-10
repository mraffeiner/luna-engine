from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response
import logging
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import pyvts
import asyncio
from pydantic import BaseModel, Field

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class BaseParamRequest(BaseModel):
    name: str


class CreateParamRequest(BaseParamRequest):
    min_val: float = Field(default=0.0, alias="min")
    max_val: float = Field(default=1.0, alias="max")
    default_value: float = 0.0
    info: str = "New Custom Parameter"


class SetParamRequest(BaseParamRequest):
    value: float = 0.0


class SetMultiParamRequest(BaseModel):
    names: list[str]
    values: list[float]


vts = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global vts

    # Configure uvicorn access logger to match application logger format
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] - %(levelname)s: %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )
    )
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(handler)
    logger.info("VTube Studio Service starting up...")
    vts = pyvts.vts(
        plugin_info={
            "plugin_name": "VTS Service",
            "developer": "Luna Engine",
            "authentication_token_path": "./token.txt",
        },
        vts_api_info={
            "host": "host.docker.internal",
            "name": "VTubeStudioPublicAPI",
            "port": 8001,
            "version": "1.0",
        },
    )
    yield
    logger.info("VTube Studio Service shutting down...")
    if vts:
        logger.info("Closing VTS API Connection..")
        await vts.close()
        logger.info("Successfully closed.")
    else:
        logger.warning("VTS API connection None, unable to close.")


# Initialize FastAPI app
app = FastAPI(
    title="VTube Studio Service API",
    description="Service for interacting with VTube Studio via pyvts.",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.info("Health check requested.")
    return {"status": "OK", "timestamp": datetime.now().isoformat()}


@app.get("/connect")
async def connect():
    global vts

    logger.info("Connecting to VTube Studio API..")
    try:
        await vts.connect()
        await vts.request_authenticate_token()
        authenticated = await vts.request_authenticate()
    except Exception:
        logger.exception("Unexpected error trying to connect to VTS API")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error trying to connect to VTS API"
        )

    if not authenticated:
        logger.error(
            "VTS authentication failed - was the plugin approved in VTube Studio?"
        )
        raise HTTPException(
            status_code=401,
            detail="VTS authentication failed - approve the plugin in VTube Studio and try again",
        )

    logger.info("Successfully connected to VTS")
    return Response(status_code=200, content="Successfully connected to VTS API")


@app.get("/list_custom_params")
async def list_custom_params():
    global vts

    logger.info("Listing tracking parameters..")
    try:
        response = await vts.request(vts.vts_request.requestTrackingParameterList())
    except Exception:
        logger.exception("Unexpected error trying to list tracking parameters")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to list tracking parameters",
        )

    data = response.get("data", {})
    if response.get("messageType") == "APIError":
        message = data.get("message", "unknown error")
        logger.error(f"VTS API error listing tracking parameters: {message}")
        raise HTTPException(
            status_code=502,
            detail=f"VTS API error listing tracking parameters: {message}",
        )

    logger.info("Successfully retrieved tracking parameters")
    return JSONResponse(
        status_code=200,
        content=data.get("customParameters", []),
    )


@app.post("/create_param")
async def create_param(request: CreateParamRequest):
    global vts

    logger.info(f"Creating custom parameter {request.name}..")
    try:
        await vts.request(
            vts.vts_request.requestCustomParameter(
                request.name,
                request.min_val,
                request.max_val,
                request.default_value,
                request.info,
            )
        )

        logger.info(f"Successfully created custom parameter {request.name}")
        return Response(
            status_code=201,
            content=f"Successfully created custom parameter {request.name}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error trying to create custom parameter {request.name}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to create custom parameter {request.name}",
        )


@app.post("/get_param")
async def get_param(request: BaseParamRequest):
    global vts

    logger.debug(f"Getting {request.name}..")
    try:
        response = await vts.request(
            vts.vts_request.requestParameterValue(request.name)
        )
        logger.debug(f"Successfully got {request.name}")
        return JSONResponse(status_code=200, content=response.get("data", {}))
    except Exception:
        logger.exception(f"Unexpected error trying to get {request.name}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to get {request.name}",
        )


@app.post("/set_param")
async def set_param(request: SetParamRequest):
    global vts

    logger.debug(f"Setting {request.name} to {request.value}..")
    try:
        await vts.request(
            vts.vts_request.requestSetParameterValue(
                request.name, request.value, face_found=True
            )
        )

        logger.debug(f"Successfully set {request.name} to {request.value}")
        return Response(
            status_code=200,
            content=f"Successfully set {request.name} to {request.value}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error trying to set {request.name} to {request.value}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to set {request.name} to {request.value}",
        )


@app.post("/set_params")
async def set_params(request: SetMultiParamRequest):
    global vts

    if len(request.names) != len(request.values):
        raise HTTPException(status_code=400, detail="names and values length mismatch")
    logger.debug(f"Setting multiple parameters {request.names} to {request.values}..")
    try:
        await vts.request(
            vts.vts_request.requestSetMultiParameterValue(
                request.names, request.values, face_found=True
            )
        )

        logger.debug(
            f"Successfully set multiple parameters {request.names} to {request.values}"
        )
        return Response(
            status_code=200,
            content=f"Successfully set multiple parameters {request.names} to {request.values}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error trying to set multiple parameters {request.names} to {request.values}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to set multiple parameters {request.names} to {request.values}",
        )


@app.delete("/delete_param")
async def delete_param(request: BaseParamRequest):
    global vts

    logger.info(f"Deleting custom parameter {request.name}..")
    try:
        await vts.request(vts.vts_request.requestDeleteCustomParameter(request.name))

        logger.info(f"Successfully deleted custom parameter {request.name}")
        return Response(status_code=204)
    except Exception:
        logger.exception(
            f"Unexpected error trying to delete custom parameter {request.name}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to delete custom parameter {request.name}",
        )
