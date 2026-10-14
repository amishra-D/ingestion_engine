from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from features.Auth.Domain.entities.user_account import UserAccount
from src.features.Auth.Application.DTO.Input.LoginDTO import LoginInputDTO
from src.features.Auth.Application.DTO.Output.LoginResponseDTO import LoginResponseDTO
from src.features.Auth.Application.use_cases.LoginUseCase import LoginUseCase
from src.features.Auth.Domain.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
)
from src.features.Auth.Presentation.routes import get_my_profile, login
from src.features.Auth.Presentation.schemas.LoginData import LoginRequest
from src.shared.security.jwt import TokenPayload


@pytest.mark.asyncio
async def test_login_use_case_success(mock_login_repo: AsyncMock, mock_token_service: AsyncMock, sample_user_account: UserAccount):
    """UseCase successfully verifies password, updates last login, and returns token."""

    # Arrange
    mock_login_repo.get_by_username.return_value = sample_user_account
    mock_token_service.generate_token.return_value = "fake.jwt.token"
    use_case = LoginUseCase(repository=mock_login_repo, token_service=mock_token_service)

    dto = LoginInputDTO(username="admin", password="securePassword123!")

    # Execute the login for the happy path
    result = await use_case.execute_login(dto)

    # Assert
    assert result.access_token == "fake.jwt.token"
    assert result.username == "admin"
    assert result.role == "ADMIN"
    assert result.user_id == 1
    mock_login_repo.get_by_username.assert_called_once_with("admin")
    mock_login_repo.update_last_login.assert_called_once_with(1)
    mock_token_service.generate_token.assert_called_once_with(
        user_id=1, username="admin", role="ADMIN"
    )


@pytest.mark.asyncio
async def test_login_use_case_wrong_password_raises_exception(
    mock_login_repo: AsyncMock, mock_token_service: AsyncMock, sample_user_account: UserAccount
):
    """UseCase raises InvalidCredentialsException if password does not match hash."""

    mock_login_repo.get_by_username.return_value = sample_user_account
    use_case = LoginUseCase(repository=mock_login_repo, token_service=mock_token_service)

    dto = LoginInputDTO(username="admin", password="wrongPassword")

    with pytest.raises(InvalidCredentialsException):
        await use_case.execute_login(dto)

    mock_login_repo.update_last_login.assert_not_called()
    mock_token_service.generate_token.assert_not_called()


@pytest.mark.asyncio
async def test_login_use_case_user_not_found_raises_exception(
    mock_login_repo: AsyncMock, mock_token_service: AsyncMock
):
    """UseCase raises InvalidCredentialsException when user is not found in database."""

    mock_login_repo.get_by_username.return_value = None
    use_case = LoginUseCase(repository=mock_login_repo, token_service=mock_token_service)

    dto = LoginInputDTO(username="unknown_user", password="anyPassword")

    with pytest.raises(InvalidCredentialsException):
        await use_case.execute_login(dto)


@pytest.mark.asyncio
async def test_login_use_case_inactive_user_raises_exception(
    mock_login_repo: AsyncMock, mock_token_service: AsyncMock, sample_inactive_user: UserAccount
):
    """UseCase raises InactiveUserException when account isActive is False."""
    mock_login_repo.get_by_username.return_value = sample_inactive_user
    use_case = LoginUseCase(repository=mock_login_repo, token_service=mock_token_service)

    dto = LoginInputDTO(username="inactive_trader", password="securePassword123!")

    with pytest.raises(InactiveUserException):
        await use_case.execute_login(dto)


@pytest.mark.asyncio
async def test_login_route_success(mock_login_use_case: AsyncMock):
    """Route maps DTO output to LoginResponse when UseCase succeeds."""

    mock_login_use_case.execute_login.return_value = LoginResponseDTO(
        access_token="mock.jwt.token",
        token_type="bearer",
        user_id=1,
        username="admin",
        role="ADMIN",
    )

    payload = LoginRequest(username="admin", password="password123")
    response = await login(payload=payload, use_case=mock_login_use_case)

    assert response.access_token == "mock.jwt.token"
    assert response.token_type == "bearer"
    assert response.username == "admin"
    assert response.role == "ADMIN"
    assert response.user_id == 1
    mock_login_use_case.execute_login.assert_called_once()


@pytest.mark.asyncio
async def test_login_route_invalid_credentials_raises_http_401(mock_login_use_case: AsyncMock):
    """Route converts domain InvalidCredentialsException into HTTP 401 Unauthorized."""
    
    mock_login_use_case.execute_login.side_effect = InvalidCredentialsException(
        "Invalid username or password"
    )

    payload = LoginRequest(username="admin", password="badPassword")

    with pytest.raises(HTTPException) as exc_info:
        await login(payload=payload, use_case=mock_login_use_case)

    assert exc_info.value.status_code == 401
    assert "Invalid username or password" in exc_info.value.detail
    assert exc_info.value.headers is not None
    assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_login_route_inactive_user_raises_http_403(mock_login_use_case: AsyncMock):
    """Route converts domain InactiveUserException into HTTP 403 Forbidden."""

    mock_login_use_case.execute_login.side_effect = InactiveUserException(
        "Account is inactive or disabled"
    )

    payload = LoginRequest(username="inactive_trader", password="password123")

    with pytest.raises(HTTPException) as exc_info:
        await login(payload=payload, use_case=mock_login_use_case)

    assert exc_info.value.status_code == 403
    assert "Account is inactive" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_my_profile_route_returns_token_payload():
    """Route directly returns the injected TokenPayload."""

    from datetime import UTC, datetime
    token_user = TokenPayload(
        sub="admin",
        user_id=1,
        role="ADMIN",
        exp=datetime.now(UTC),
    )

    result = await get_my_profile(current_user=token_user)

    assert result.sub == "admin"
    assert result.role == "ADMIN"
    assert result.user_id == 1
