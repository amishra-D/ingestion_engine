from abc import ABC, abstractmethod


class ITokenService(ABC):
    @abstractmethod
    def generate_token(self, user_id: int, username: str, role: str) -> str:
        """Generates an access token containing the given user claims."""
