import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.features.Auth.Application.ports.LoginRepository import ILoginRepository
from src.features.Auth.Application.ports.TokenService import ITokenService
from src.features.Auth.Application.use_cases.LoginUseCase import LoginUseCase
from src.features.Auth.Domain.entities.user_account import UserAccount
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    PaginationOutDto,
    TradeBookOutDto,
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)
from src.features.Tradebook.Application.use_cases.get_trade import GetTradeUseCase
from src.shared.security.jwt import TokenPayload, create_access_token


# =====================================================================
# 1. Mock Ports & Use Cases (Pure Unit Test Mocks)
# =====================================================================
@pytest.fixture
def mock_login_repo():
    """Mock for ILoginRepository port."""
    return AsyncMock(spec=ILoginRepository)


@pytest.fixture
def mock_token_service():
    """Mock for ITokenService port."""
    return AsyncMock(spec=ITokenService)


@pytest.fixture
def mock_login_use_case():
    """Mock for LoginUseCase to unit test routes directly."""
    return AsyncMock(spec=LoginUseCase)


@pytest.fixture
def mock_trade_repo():
    """Mock for IGetTradesRepository port."""
    repo = AsyncMock(spec=IGetTradesRepository)
    repo.execute_get_trade.return_value = TradeBookPageOutDto(
        data=[
            TradeBookOutDto(
                trade_id=5609,
                member_code="MEM001",
                symbol="BANKNIFTY",
                quantity=30,
                price=Decimal("178.170000"),
                trade_time=datetime.now(UTC),
            )
        ],
        pagination=PaginationOutDto(
            cursor_start=5609,
            cursor_end=5609,
            has_prev=False,
            has_next=False,
        ),
    )
    return repo


@pytest.fixture
def mock_trade_use_case():
    """Mock for GetTradeUseCase to unit test routes directly."""
    return AsyncMock(spec=GetTradeUseCase)


@pytest.fixture
def admin_token():
    return create_access_token(
        username="admin", user_id=1, role="ADMIN"
    )


@pytest.fixture
def dealer_token():
    return create_access_token(
        username="SUP", user_id=2, role="DEALER"
    )


@pytest.fixture
def broker_token():
    return create_access_token(
        username="broker1", user_id=4, role="BROKER"
    )


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def dealer_headers(dealer_token):
    return {"Authorization": f"Bearer {dealer_token}"}


@pytest.fixture
def broker_headers(broker_token):
    return {"Authorization": f"Bearer {broker_token}"}


@pytest.fixture
def sample_user_account():
    """Active user account with password 'securePassword123!'."""
    password_hash = hashlib.sha512("securePassword123!".encode("utf-8")).digest()
    return UserAccount(
        user_id=1,
        username="admin",
        password_hash=password_hash,
        role="ADMIN",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_login_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_inactive_user():
    """Inactive user account with password 'securePassword123!'."""
    password_hash = hashlib.sha512("securePassword123!".encode("utf-8")).digest()
    return UserAccount(
        user_id=99,
        username="inactive_trader",
        password_hash=password_hash,
        role="DEALER",
        is_active=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_login_at=datetime.now(UTC),
    )