"""
API v1 endpoints.
"""

from .consent import router as consent_router
from .students import router as students_router
from .standards import router as standards_router
from .assessments import router as assessments_router

__all__ = [
    "consent_router",
    "students_router",
    "standards_router",
    "assessments_router",
]
