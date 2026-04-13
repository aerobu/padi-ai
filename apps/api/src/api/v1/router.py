"""
API v1 Router.
Contains all v1 API endpoints organized by resource.
"""

from fastapi import APIRouter

from . import health

router = APIRouter()

# Include health endpoints
router.include_router(health.router, prefix="/health", tags=["Health"])
