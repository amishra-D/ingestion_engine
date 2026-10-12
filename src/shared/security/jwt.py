from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pydantic import BaseModel

from src.shared.config.settings import settings


class TokenPayload(BaseModel):
    sub: str          # Username
    user_id: int      # UserId
    role: str         # Role ('ADMIN', 'BROKER', 'DEALER', 'GROUP')
    exp: datetime


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(hours=8))

    payload: dict[str, Any] = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return TokenPayload(**decoded)
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid or expired token: {e!s}") from e
