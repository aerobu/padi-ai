"""
API v1 Router.
Contains all v1 API endpoints organized by resource.
"""

from fastapi import APIRouter

from . import health
from .endpoints import (
    consent_router,
    students_router,
    standards_router,
    assessments_router,
)

router = APIRouter()

# Include health endpoints
router.include_router(health.router, prefix="/health", tags=["Health"])

# Include consent endpoints
router.include_router(
    consent_router,
    tags=["Consent"],
)

# Include student endpoints
router.include_router(
    students_router,
    tags=["Students"],
)

# Include standards endpoints
router.include_router(
    standards_router,
    tags=["Standards"],
)

# Include assessment endpoints
router.include_router(
    assessments_router,
    tags=["Assessments"],
)
