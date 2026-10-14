from fastapi import Request
from fastapi.responses import JSONResponse

from src.features.Tradebook.Domain.exceptions import (
    TradebookException,
    PrivilegeEscalationException,
    UnauthorizedUserAccessException,
)


def map_tradebook_exception(
    exc: TradebookException,
) -> tuple[int, str, str]:
    
    if isinstance(exc, PrivilegeEscalationException):
        return (
            403,
            "PRIVILEGE_ESCALATION",
            str(exc),
        )

    if isinstance(exc, UnauthorizedUserAccessException):
        return (
            403,
            "UNAUTHORIZED_USER_ACCESS",
            str(exc),
        )

    return (
        400,
        "TRADEBOOK_ERROR",
        str(exc),
    )

async def tradebook_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:

    # FastAPI registers this handler for TradebookException.
    # This guard also makes the expected type explicit.
    if not isinstance(exc, TradebookException):
        raise exc

    status_code, error_code, message = map_tradebook_exception(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_code,
            "message": message,
        },
    )