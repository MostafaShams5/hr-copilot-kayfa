"""Custom exception classes and error handlers."""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class CVScreeningException(Exception):
    """Base exception for CV Screening Agent."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidFileTypeError(CVScreeningException):
    """Raised when file type is not supported."""

    def __init__(self, message: str, received_type: str | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_TYPE",
            details={"received": received_type} if received_type else {},
        )


class FileTooLargeError(CVScreeningException):
    """Raised when file exceeds size limit."""

    def __init__(self, message: str, max_size_mb: int | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            details={"max_size_mb": max_size_mb} if max_size_mb else {},
        )


class MissingFileError(CVScreeningException):
    """Raised when required file is missing."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="MISSING_FILE",
        )


class InvalidJobRequisitionError(Exception):
    """Raised when job requisition is invalid."""
    
    def __init__(self, message: str, status_code: int = 422, details: dict = None):
        self.message = message
        self.status_code = status_code  
        self.details = details or {}
        super().__init__(self.message)


class ScreeningAgentError(CVScreeningException):
    """Raised when agent screening fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SCREENING_FAILED",
            details=details or {},
        )


class UnauthorizedError(CVScreeningException):
    """Raised when bearer token is missing or invalid."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


def format_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format error response."""
    return {
        "error": {
            "code": error_code,
            "message": message,
            **({"details": details} if details else {}),
        }
    }


async def cv_screening_exception_handler(
    request: Request,
    exc: CVScreeningException,
) -> JSONResponse:
    """Handle CVScreeningException."""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.error_code, exc.message, exc.details),
    )


async def validation_error_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle Pydantic ValidationError."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            "VALIDATION_ERROR",
            "Request validation failed",
            {"errors": exc.errors()},
        ),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            {"detail": str(exc)},
        ),
    )