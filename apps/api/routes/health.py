"""Health check route for the Commerce AI Platform."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="ok",
        service="commerce-ai-platform",
    )