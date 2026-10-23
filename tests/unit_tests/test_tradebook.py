from unittest.mock import AsyncMock

import pytest
from datetime import UTC, datetime
from decimal import Decimal
from fastapi import HTTPException

from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    PaginationOutDto,
    TradeBookOutDto,
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.use_cases.get_trade import GetTradeUseCase
from src.features.Tradebook.Domain.exceptions import (
    PrivilegeEscalationException,
    UnauthorizedUserAccessException,
)
from src.features.Tradebook.Presentation.routers import get_tradebook_req
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.shared.security.jwt import TokenPayload


@pytest.mark.asyncio
async def test_get_trade_use_case_success(mock_trade_repo: AsyncMock):
    """UseCase enforces policy, builds TradeBookDTO, and returns page from repo."""

    use_case = GetTradeUseCase(repository=mock_trade_repo)

    current_user = TokenPayload(
        sub="SUP", user_id=2, role="DEALER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="DEALER", userid="SUP", limit=10)

    result = await use_case.execute_get_trade(query, current_user)

    assert len(result.data) == 1
    assert result.data[0].trade_id == 5609
    assert result.pagination.cursor_start == 5609
    mock_trade_repo.execute_get_trade.assert_called_once()  # Infrastructure layer repository calling


@pytest.mark.asyncio
async def test_get_trade_use_case_escalation_denied(mock_trade_repo: AsyncMock):
    """UseCase raises PrivilegeEscalationException when dealer requests admin."""

    use_case = GetTradeUseCase(repository=mock_trade_repo)

    current_user = TokenPayload(
        sub="SUP", user_id=2, role="DEALER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="ADMIN", userid="SUP", limit=10)

    with pytest.raises(PrivilegeEscalationException):
        await use_case.execute_get_trade(query, current_user)

    mock_trade_repo.execute_get_trade.assert_not_called()


@pytest.mark.asyncio
async def test_get_trade_use_case_snooping_denied(mock_trade_repo: AsyncMock):
    """UseCase raises UnauthorizedUserAccessException when dealer requests another dealer."""
    use_case = GetTradeUseCase(repository=mock_trade_repo)

    current_user = TokenPayload(
        sub="SUP", user_id=2, role="DEALER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="DEALER", userid="D001", limit=10)

    with pytest.raises(UnauthorizedUserAccessException):
        await use_case.execute_get_trade(query, current_user)

    mock_trade_repo.execute_get_trade.assert_not_called()


@pytest.mark.asyncio
async def test_get_tradebook_route_success(mock_trade_use_case: AsyncMock):
    """Route directly returns TradeBookPageOutDto from UseCase."""
    mock_trade_use_case.execute_get_trade.return_value = TradeBookPageOutDto(
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

    current_user = TokenPayload(
        sub="SUP", user_id=2, role="DEALER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="DEALER", userid="SUP")

    response = await get_tradebook_req(
        user_query=query,
        current_user=current_user,
        use_case=mock_trade_use_case,
    )

    assert len(response.data) == 1
    assert response.data[0].trade_id == 5609
    assert response.pagination.cursor_start == 5609


@pytest.mark.asyncio
async def test_get_tradebook_route_catches_tradebook_exception_as_403(
    mock_trade_use_case: AsyncMock,
):
    """Route catches TradebookException and translates to HTTP 403 Forbidden."""
    mock_trade_use_case.execute_get_trade.side_effect = PrivilegeEscalationException(
        current_role="DEALER", target_role="ADMIN"
    )

    current_user = TokenPayload(
        sub="SUP", user_id=2, role="DEALER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="ADMIN", userid="SUP")

    with pytest.raises(HTTPException) as exc_info:
        await get_tradebook_req(
            user_query=query,
            current_user=current_user,
            use_case=mock_trade_use_case,
        )

    assert exc_info.value.status_code == 403
    assert "Privilege escalation denied" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_trade_use_case_broker_views_all_dealers(mock_trade_repo: AsyncMock):
    """Broker querying an account code does not have username injected as dealer ID."""
    use_case = GetTradeUseCase(repository=mock_trade_repo)

    current_user = TokenPayload(
        sub="broker1", user_id=4, role="BROKER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="BROKER", accountcode="90068", limit=10)

    await use_case.execute_get_trade(query, current_user)

    mock_trade_repo.execute_get_trade.assert_called_once()
    dto = mock_trade_repo.execute_get_trade.call_args[0][0]
    assert dto.user.role == "BROKER"
    assert dto.user.accountcode == "90068"
    assert dto.user.userid is None


@pytest.mark.asyncio
async def test_get_trade_use_case_broker_views_specific_dealer(
    mock_trade_repo: AsyncMock,
):
    """Broker querying a specific dealer passes that dealer's ID to repository."""
    use_case = GetTradeUseCase(repository=mock_trade_repo)

    current_user = TokenPayload(
        sub="broker1", user_id=4, role="BROKER", exp=datetime.now(UTC)
    )
    query = UserRequest(role="BROKER", accountcode="90068", userid="SUP", limit=10)

    await use_case.execute_get_trade(query, current_user)

    mock_trade_repo.execute_get_trade.assert_called_once()
    dto = mock_trade_repo.execute_get_trade.call_args[0][0]
    assert dto.user.role == "BROKER"
    assert dto.user.accountcode == "90068"
    assert dto.user.userid == "SUP"


def test_user_request_field_aliases():
    """UserRequest accepts both snake_case and lowercase field names."""
    req = UserRequest(accountcode="90068", userid="SUP", groupcode="HO")
    assert req.accountcode == "90068"
    assert req.userid == "SUP"
    assert req.groupcode == "HO"
