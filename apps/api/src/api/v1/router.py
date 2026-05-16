"""
API v1 Router.
Contains all v1 API endpoints organized by resource.
"""

from fastapi import APIRouter

from . import health
from .endpoints import (
    assessments_router,
    auth_router,
    consent_router,
    generation_jobs_router,
    learning_plans_router,
    parent,
    standards_router,
    students_router,
)
from .endpoints import practice_ws

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

# Include auth endpoints
router.include_router(
    auth_router,
    tags=["Auth"],
)

# Include learning plans endpoints
router.include_router(
    learning_plans_router,
    tags=["Learning Plans"],
)

# Include generation jobs endpoints
router.include_router(
    generation_jobs_router,
    prefix="/admin",
    tags=["Admin - Generation Jobs"],
)

# Include parent dashboard endpoints
router.include_router(
    parent.router,
    tags=["Parent Dashboard"],
)

# Adaptive-practice WebSocket session (Stage 3)
router.include_router(
    practice_ws.router,
    tags=["Practice Session (WebSocket)"],
)
