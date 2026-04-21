"""
API v1 endpoints.
"""

from .consent import router as consent_router
from .students import router as students_router
from .standards import router as standards_router
from .assessments import router as assessments_router
from .auth import router as auth_router
from .learning_plans import router as learning_plans_router
from .generation_jobs import router as generation_jobs_router
from . import parent

__all__ = [
    "consent_router",
    "students_router",
    "standards_router",
    "assessments_router",
    "auth_router",
    "learning_plans_router",
    "generation_jobs_router",
    "parent",
]
