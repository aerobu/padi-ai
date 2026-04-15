"""
Generic API response wrapper.
"""

from typing import Generic, TypeVar

T = TypeVar("T")


class ApiResponse(Generic[T]):
    """Generic API response structure."""

    success: bool
    data: T | None = None
    error: dict | None = None

    @classmethod
    def success_response(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def error_response(cls, code: str, message: str) -> "ApiResponse[T]":
        return cls(success=False, error={"code": code, "message": message})
