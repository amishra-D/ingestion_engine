from src.features.Auth.Application.ports.TokenService import ITokenService
from src.shared.security.jwt import create_access_token


class JwtTokenService(ITokenService):
    def generate_token(self, user_id: int, username: str, role: str) -> str:
        return create_access_token(
            user_id=user_id,
            username=username,
            role=role,
        )
