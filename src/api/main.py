from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from loguru import logger
from starlette.status import (
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from src.api.config import APISettings, get_api_settings
from src.api.file_ingestion.router import file_ingestion_router
from src.database.engine import check_db_connection, DBConnectionError

# Here put the routers you want to add to the app
ROUTERS = (file_ingestion_router,)

# ----------------------------------------------------------------- #
# App creation methods                                              #
# ----------------------------------------------------------------- #


def create_app(settings: APISettings | None = None) -> FastAPI:
    """FastAPI app creation method, to use settings in the creation
    since FastAPI doesn't allow for dependencies to be resolved before app creation.

    Args:
        settings (APISettings): settings of api needed to configure FastAPI app

    Returns:
        FastAPI app
    """
    if settings is None:
        settings = get_api_settings()

    return FastAPI(
        title="API Ingestion de fichiers",
        description="API Ingestion de fichiers",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        root_path=f"/api/{settings.api_version}",
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting API...")
    # todo check db exists and is created
    yield  # Startup complete, application ready
    logger.info("Shutting down API...")


# ----------------------------------------------------------------- #
# App and Routers creation                                          #
# ----------------------------------------------------------------- #

# Create FastAPI application
app = create_app()

# Include routers to the app
for router in ROUTERS:
    app.include_router(router)

# ----------------------------------------------------------------- #
# App root endpoints (needs app to be created already)              #
# ----------------------------------------------------------------- #


@app.get("/")
async def root(settings: APISettings = Depends(get_api_settings)):
    """Root endpoint"""
    return {
        "service": "API Ingestion de fichiers",
        "version": settings.api_version,
        "status": "running",
    }


@app.get("/health")
async def health(settings: APISettings = Depends(get_api_settings)):
    """Health endpoint"""
    try:
        check_db_connection(settings.database_url)
        return {"status": "database ready"}
    except DBConnectionError as e:
        return HTTPException(HTTP_503_SERVICE_UNAVAILABLE, f"DB unavailable: {str(e)}")
    except Exception as e:
        return HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
