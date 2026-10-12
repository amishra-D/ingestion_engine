import asyncio
import hashlib
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException

from src.features.Auth.Application.DTO.Input.LoginDTO import LoginInputDTO
from src.features.Auth.Application.ports.LoginRepository import ILoginRepository
from src.features.Auth.Application.ports.TokenService import ITokenService
from src.features.Auth.Application.use_cases.LoginUseCase import LoginUseCase
from src.features.Auth.Domain.entities.user_account import UserAccount
from src.features.Auth.Domain.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
)
from src.features.Auth.Infrastructure.services.JwtTokenService import JwtTokenService
from src.shared.security.dependencies import require_roles
from src.shared.security.jwt import TokenPayload, decode_access_token


class TestAuthCleanArchitecture(unittest.TestCase):
    def setUp(self):
        self.plain_password = "securePassword123!"
        self.password_hash_64 = hashlib.sha512(self.plain_password.encode("utf-8")).digest()
        self.user = UserAccount(
            user_id=101,
            username="trader_john",
            password_hash=self.password_hash_64,
            role="DEALER",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_login_at=datetime.now(UTC),
        )
        self.token_service = JwtTokenService()

    def test_domain_password_verification(self):
        self.assertTrue(self.user.verify_password(self.plain_password))
        self.assertFalse(self.user.verify_password("wrongPassword"))

    def test_jwt_token_creation_and_claims(self):
        token = self.token_service.generate_token(
            user_id=self.user.user_id,
            username=self.user.username,
            role=self.user.role,
        )
        payload = decode_access_token(token)
        self.assertEqual(payload.user_id, 101)
        self.assertEqual(payload.sub, "trader_john")
        self.assertEqual(payload.role, "DEALER")

    def test_login_use_case_success_with_token_service(self):
        mock_repo = AsyncMock(spec=ILoginRepository)
        mock_repo.get_by_username.return_value = self.user
        mock_repo.update_last_login.return_value = None

        mock_token_service = MagicMock(spec=ITokenService)
        mock_token_service.generate_token.return_value = "mocked_jwt_token"

        use_case = LoginUseCase(repository=mock_repo, token_service=mock_token_service)
        dto = LoginInputDTO(username="trader_john", password=self.plain_password)

        res = asyncio.run(use_case.execute_login(dto))
        self.assertEqual(res.username, "trader_john")
        self.assertEqual(res.role, "DEALER")
        self.assertEqual(res.user_id, 101)
        self.assertEqual(res.access_token, "mocked_jwt_token")
        mock_repo.update_last_login.assert_awaited_once_with(101)
        mock_token_service.generate_token.assert_called_once_with(
            user_id=101, username="trader_john", role="DEALER"
        )

    def test_login_use_case_invalid_password(self):
        mock_repo = AsyncMock(spec=ILoginRepository)
        mock_repo.get_by_username.return_value = self.user
        mock_token_service = MagicMock(spec=ITokenService)

        use_case = LoginUseCase(repository=mock_repo, token_service=mock_token_service)
        dto = LoginInputDTO(username="trader_john", password="bad_password")

        with self.assertRaises(InvalidCredentialsException):
            asyncio.run(use_case.execute_login(dto))

    def test_login_use_case_inactive_user(self):
        inactive_user = UserAccount(
            user_id=102,
            username="inactive_trader",
            password_hash=self.password_hash_64,
            role="BROKER",
            is_active=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_login_at=datetime.now(UTC),
        )
        mock_repo = AsyncMock(spec=ILoginRepository)
        mock_repo.get_by_username.return_value = inactive_user
        mock_token_service = MagicMock(spec=ITokenService)

        use_case = LoginUseCase(repository=mock_repo, token_service=mock_token_service)
        dto = LoginInputDTO(username="inactive_trader", password=self.plain_password)

        with self.assertRaises(InactiveUserException):
            asyncio.run(use_case.execute_login(dto))

    def test_shared_rbac_allowed_role(self):
        # RBAC allows DEALER when DEALER is in allowed list
        checker = require_roles(["ADMIN", "DEALER"])
        user_payload = TokenPayload(
            sub="trader_john",
            user_id=101,
            role="DEALER",
            exp=datetime.now(UTC),
        )
        checked_user = asyncio.run(checker(user_payload))
        self.assertEqual(checked_user.role, "DEALER")

    def test_shared_rbac_denied_role(self):
        # RBAC denies DEALER if route only allows ADMIN
        checker = require_roles(["ADMIN"])
        user_payload = TokenPayload(
            sub="trader_john",
            user_id=101,
            role="DEALER",
            exp=datetime.now(UTC),
        )
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(checker(user_payload))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access denied", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
