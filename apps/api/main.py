"""Commerce AI Platform — FastAPI application entry point.

Registers route modules and configures request/response logging
middleware for traceability.
"""

import logging
import time

from fastapi import FastAPI, Request

from apps.api.routes.health import router as health_router
from apps.api.routes.videos import router as videos_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Commerce AI Platform")

app.include_router(health_router)
app.include_router(videos_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every inbound request and its response status for traceability."""
    start = time.perf_counter()
    logger.info(
        "Request: method=%s path=%s",
        request.method,
        request.url.path,
    )
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Response: method=%s path=%s status=%d duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/")
def root():
    """Root health-check endpoint."""
    return {"status": "ok"}