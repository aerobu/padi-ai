"""
Generic API response wrapper.
"""

from typing import Generic, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response structure."""

    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None

    @classmethod
    def success_response(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def error_response(cls, code: str, message: str) -> "ApiResponse[T]":
        return cls(success=False, error={"code": code, "message": message})
