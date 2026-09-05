"""Dependency injection for FastAPI."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.api.errors import UnauthorizedError
from app.config import settings
from app.agents import screening_agent
import logging

logger = logging.getLogger(__name__)


async def verify_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Verify bearer token from Authorization header.
    
    Validates format only; actual auth/RBAC is upstream.
    """
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")

    # Expected format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError(
            "Invalid Authorization header format. Expected: Bearer <token>"
        )

    token = parts[1]
    if not token or len(token) < 5:
        raise UnauthorizedError("Invalid token format")

    return token


async def get_screening_agent():
    """Get or create screening agent instance."""
    from app.agents.screening_agent import ScreeningAgent

    agent = ScreeningAgent()
    return agent


# Dependency aliases for readability
BearerToken = Annotated[str, Depends(verify_bearer_token)]
ScreeningAgentDep = Annotated[
    "screening_agent", Depends(get_screening_agent)
]

async def bearer_token_optional(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Optional bearer token for development.
    In production, this will be enforced.
    """
    if settings.ENV == "prod":
        # Production: require token
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
            )
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format",
            )
        return authorization.split(" ")[1]
    
    # Development: token is optional
    if authorization:
        if authorization.startswith("Bearer "):
            return authorization.split(" ")[1]
        return authorization
    
    return "dev-token"  # Default for development


# Type alias for dependency injection
BearerToken = Annotated[str, Depends(bearer_token_optional)]