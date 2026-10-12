from fastapi import APIRouter, Depends, HTTPException, status

from src.features.Auth.Application.DTO.Input.LoginDTO import LoginInputDTO
from src.features.Auth.Application.use_cases.LoginUseCase import LoginUseCase
from src.features.Auth.Domain.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
)
from src.features.Auth.Infrastructure.repositories.LoginRepository import (
    LoginRepository,
)
from src.features.Auth.Infrastructure.services.JwtTokenService import (
    JwtTokenService,
)
from src.features.Auth.Presentation.schemas.LoginData import (
    LoginRequest,
    LoginResponse,
)
from src.shared.database.connection import db
from src.shared.security.dependencies import TokenPayload, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_login_use_case() -> LoginUseCase:
    repo = LoginRepository(db)
    token_service = JwtTokenService()
    return LoginUseCase(repository=repo, token_service=token_service)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
):
    try:
        dto = LoginInputDTO(username=payload.username, password=payload.password)
        result = await use_case.execute_login(dto)
        return LoginResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            user_id=result.user_id,
            username=result.username,
            role=result.role,
        )
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/me", response_model=TokenPayload)
async def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Returns the authenticated user details from the token."""
    return current_user
