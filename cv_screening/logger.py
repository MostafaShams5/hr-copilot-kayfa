"""Structured logging setup with Pydantic Logfire."""

import sys
from typing import Any

try:
    import logfire

    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from app.config import settings


def setup_logger() -> None:
    """Initialize Pydantic Logfire or fallback to standard logging."""
    if not LOGFIRE_AVAILABLE:
        print("Logfire not available, using standard Python logging")
        return

    if not settings.LOGFIRE_ENABLED:
        print("ℹLogfire disabled via config")
        return

    try:
        logfire.configure(
            project_name=settings.LOGFIRE_PROJECT_NAME,
            token=settings.LOGFIRE_TOKEN,
            service_name=settings.APP_NAME,
            service_version=settings.APP_VERSION,
            environment=settings.ENV,
        )
        print("✓ Logfire configured successfully")
    except Exception as e:
        print(f"⚠️  Failed to configure Logfire: {e}")


def log_info(message: str, **kwargs: Any) -> None:
    """Log an info message."""
    if LOGFIRE_AVAILABLE and settings.LOGFIRE_ENABLED:
        logfire.info(message, **kwargs)
    else:
        print(f"[INFO] {message}", file=sys.stdout)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    if LOGFIRE_AVAILABLE and settings.LOGFIRE_ENABLED:
        logfire.warning(message, **kwargs)
    else:
        print(f"[WARNING] {message}", file=sys.stdout)


def log_error(message: str, exception: Exception = None, **kwargs: Any) -> None:
    """Log an error message."""
    if LOGFIRE_AVAILABLE and settings.LOGFIRE_ENABLED:
        if exception:
            logfire.error(message, exc_info=exception, **kwargs)
        else:
            logfire.error(message, **kwargs)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)
        if exception:
            print(f"  Exception: {exception}", file=sys.stderr)


def log_debug(message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    if LOGFIRE_AVAILABLE and settings.LOGFIRE_ENABLED:
        logfire.debug(message, **kwargs)
    else:
        if settings.DEBUG:
            print(f"[DEBUG] {message}", file=sys.stdout)


class LogContext:
    """Context manager for structured logging."""

    def __init__(self, operation: str, **context: Any):
        self.operation = operation
        self.context = context

    def __enter__(self):
        log_info(f"Starting: {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            log_error(
                f"Failed: {self.operation}",
                exception=exc_val,
                **self.context,
            )
        else:
            log_info(f"Completed: {self.operation}", **self.context)
