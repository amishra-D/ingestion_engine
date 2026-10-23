from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.shared.security.jwt import TokenPayload, decode_access_token

## The module follows the dependency queue as
# 1. get_user_role-> get_current_user
# 2. require_roles -> get_current_user
# 3. get_current_user -> Bearer Scheme

bearer_scheme = HTTPBearer(auto_error=True)


# Central dependency to get the current user payload from the accesstoken
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenPayload:
    """Extracts, verifies JWT token and returns authenticated user payload."""
    try:
        token = credentials.credentials
        return decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# Checks the role based on the given access token
def require_roles(allowed_roles: Sequence[str]):
    """Role-based authorization dependency factory."""

    async def role_checker(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        if user.role.upper() not in [r.upper() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user.role}' not permitted.",
            )
        return user

    return role_checker


# Fetch the user role based on the get current user dependency
async def get_user_role(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> str:
    """Returns the authenticated user's role directly."""
    return user.role
