from abc import ABC, abstractmethod

from src.features.Auth.Domain.entities.user_account import UserAccount


class ILoginRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> UserAccount | None:
        """Fetch user account by username."""

    @abstractmethod
    async def update_last_login(self, user_id: int) -> None:
        """Update last login timestamp in UTC."""
