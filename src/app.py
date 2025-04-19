from contextlib import asynccontextmanager
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


class CreateParamRequest(BaseModel):
    name: str
    min_val: float = Field(default=0.0, alias="min")
    max_val: float = Field(default=1.0, alias="max")
    default_value: float = 0.0
    info: str = "New Custom Parameter"


class SetParamRequest(BaseModel):
    name: str
    value: float = 0.0


class DeleteParamRequest(BaseModel):
    name: str


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
            "developer": "TastiHam",
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


@app.get("/connect")
async def connect():
    global vts

    logger.info("Connecting to VTube Studio API..")
    try:
        await vts.connect()
        await vts.request_authenticate_token()
        await vts.request_authenticate()
    except Exception:
        logger.exception("Unexpected error trying to connect to VTS API")
        return HTTPException(
            status_code=500, detail=f"Unexpected error trying to connect to VTS API"
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
        return HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to list tracking parameters",
        )
    logger.info("Successfully retrieved tracking parameters")
    return JSONResponse(
        status_code=200, content=response.get("data", {}).get("customParameters", {})
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
    except Exception:
        logger.exception(
            f"Unexpected error trying to create custom parameter {request.name}"
        )
        return HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to create custom parameter {request.name}",
        )
    logger.info(f"Successfully created custom parameter {request.name}")
    return Response(
        status_code=201, content=f"Successfully created custom parameter {request.name}"
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
    except Exception:
        logger.exception(
            f"Unexpected error trying to set {request.name} to {request.value}"
        )
        return HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to set {request.name} to {request.value}",
        )
    logger.debug(f"Successfully set {request.name} to {request.value}")
    return Response(
        status_code=200, content=f"Successfully set {request.name} to {request.value}"
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
    except Exception:
        logger.exception(
            f"Unexpected error trying to set multiple parameters {request.names} to {request.values}"
        )
        return HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to set multiple parameters {request.names} to {request.values}",
        )
    logger.debug(
        f"Successfully set multiple parameters {request.names} to {request.values}"
    )
    return Response(
        status_code=200,
        content=f"Successfully set multiple parameters {request.names} to {request.values}",
    )


@app.delete("/delete_param")
async def delete_param(request: DeleteParamRequest):
    global vts

    logger.info(f"Deleting custom parameter {request.name}..")
    try:
        await vts.request(vts.vts_request.requestDeleteCustomParameter(request.name))
    except Exception:
        logger.exception(
            f"Unexpected error trying to delete custom parameter {request.name}"
        )
        return HTTPException(
            status_code=500,
            detail=f"Unexpected error trying to delete custom parameter {request.name}",
        )
    logger.info(f"Successfully deleted custom parameter {request.name}")
    return Response(status_code=204)
