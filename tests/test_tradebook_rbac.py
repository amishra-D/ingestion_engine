import asyncio
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from fastapi import HTTPException

from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    PaginationOutDto,
    TradeBookOutDto,
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.use_cases.get_trade import GetTradeUseCase
from src.features.Tradebook.Presentation.routers import get_tradebook_req
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.shared.security.jwt import TokenPayload


class TestTradebookRBACPrivileges(unittest.TestCase):
    def setUp(self):
        self.mock_use_case = AsyncMock(spec=GetTradeUseCase)
        self.mock_use_case.execute_get_trade.return_value = TradeBookPageOutDto(
            data=[
                TradeBookOutDto(
                    trade_id=1,
                    member_code="MEM01",
                    symbol="RELIANCE",
                    quantity=100,
                    price=Decimal("2500.0"),
                    trade_time=datetime.now(UTC),
                )
            ],
            pagination=PaginationOutDto(
                cursor_start=1,
                cursor_end=1,
                has_prev=False,
                has_next=False,
            ),
        )

    def test_dealer_cannot_escalate_to_admin(self):
        # Authenticated as DEALER 'SUP'
        dealer_token = TokenPayload(
            sub="SUP",
            user_id=2,
            role="DEALER",
            exp=datetime.now(UTC),
        )
        # Tries to request ADMIN role in body
        malicious_query = UserRequest(role="ADMIN", userid="SUP")

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                get_tradebook_req(
                    user_query=malicious_query,
                    current_user=dealer_token,
                    use_case=self.mock_use_case,
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Privilege escalation denied", ctx.exception.detail)

    def test_dealer_cannot_access_other_dealer_trades(self):
        # Authenticated as DEALER 'SUP'
        dealer_token = TokenPayload(
            sub="SUP",
            user_id=2,
            role="DEALER",
            exp=datetime.now(UTC),
        )
        # Tries to query trades of dealer 'D001'
        snooping_query = UserRequest(role="DEALER", userid="D001")

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                get_tradebook_req(
                    user_query=snooping_query,
                    current_user=dealer_token,
                    use_case=self.mock_use_case,
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access denied", ctx.exception.detail)
        self.assertIn("D001", ctx.exception.detail)

    def test_broker_cannot_escalate_to_admin(self):
        # Authenticated as BROKER 'broker1'
        broker_token = TokenPayload(
            sub="broker1",
            user_id=4,
            role="BROKER",
            exp=datetime.now(UTC),
        )
        malicious_query = UserRequest(role="ADMIN", accountcode="90068")

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                get_tradebook_req(
                    user_query=malicious_query,
                    current_user=broker_token,
                    use_case=self.mock_use_case,
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Privilege escalation denied", ctx.exception.detail)

    def test_dealer_allowed_to_query_own_trades(self):
        dealer_token = TokenPayload(
            sub="SUP",
            user_id=2,
            role="DEALER",
            exp=datetime.now(UTC),
        )
        legit_query = UserRequest(role="DEALER", userid="SUP")

        res = asyncio.run(
            get_tradebook_req(
                user_query=legit_query,
                current_user=dealer_token,
                use_case=self.mock_use_case,
            )
        )
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.pagination.cursor_start, 1)
        # Ensure the use case was called with verified dealer credentials
        called_args = self.mock_use_case.execute_get_trade.call_args[0][0]
        self.assertEqual(called_args.user.role, "DEALER")
        self.assertEqual(called_args.user.userid, "SUP")

    def test_admin_allowed_to_query_all(self):
        admin_token = TokenPayload(
            sub="admin",
            user_id=1,
            role="ADMIN",
            exp=datetime.now(UTC),
        )
        admin_query = UserRequest(role="ADMIN", userid="")

        res = asyncio.run(
            get_tradebook_req(
                user_query=admin_query,
                current_user=admin_token,
                use_case=self.mock_use_case,
            )
        )
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.pagination.cursor_end, 1)
        called_args = self.mock_use_case.execute_get_trade.call_args[0][0]
        self.assertEqual(called_args.user.role, "ADMIN")


if __name__ == "__main__":
    unittest.main()

