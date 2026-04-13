"""
Health Check Endpoints.
Provides various health check routes for monitoring and load balancers.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ...clients.llm_client import get_llm_client

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="Basic health check endpoint for the API.",
)
async def health_check() -> dict:
    """
    Basic health check endpoint.
    Returns 200 OK if the API is running.
    """
    return {
        "status": "ok",
        "service": "padi-api",
        "version": "0.1.0",
    }


@router.get(
    "/llm",
    status_code=status.HTTP_200_OK,
    summary="LLM Health Check",
    description="Health check for LLM connectivity.",
)
async def llm_health_check() -> dict:
    """
    LLM health check endpoint.
    Verifies connection to local Ollama instance.
    """
    llm_client = get_llm_client()
    return llm_client.get_health()


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Kubernetes readiness probe endpoint.",
)
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint.
    Returns 200 if the API is ready to serve requests.
    """
    from sqlalchemy import text

    try:
        from src.core.config import get_settings

        settings = get_settings()
        from sqlalchemy import create_engine

        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready", "database": db_status},
    )


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Kubernetes liveness probe endpoint.",
)
async def liveness_check() -> JSONResponse:
    """
    Liveness check endpoint.
    Returns 200 if the API process is alive.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"},
    )
