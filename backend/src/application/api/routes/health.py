"""Health check API routes."""

from datetime import datetime
from fastapi import APIRouter
from src.application.api.dto import HealthCheckResponse
from src.infrastructure.config import infrastructure_config

router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    health_status = await infrastructure_config.health_check()

    return HealthCheckResponse(
        status=health_status["status"],
        timestamp=datetime.utcnow(),
        services=health_status["services"],
        version="1.0.0",
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        health_status = await infrastructure_config.health_check()
        if health_status["status"] == "healthy":
            return {"status": "ready"}
        else:
            return {"status": "not ready", "details": health_status["services"]}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}
