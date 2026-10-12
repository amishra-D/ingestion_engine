
from src.features.Auth.Application.ports.LoginRepository import ILoginRepository
from src.features.Auth.Domain.entities.user_account import UserAccount
from src.shared.database.connection import Database


class LoginRepository(ILoginRepository):
    def __init__(self, database: Database):
        self.database = database

    async def get_by_username(self, username: str) -> UserAccount | None:
        query = """
            SELECT UserId, Username, PasswordHash, Role, isActive, CreatedAt, UpdatedAt, LastLoginAt
            FROM [dbo].[UserAccount]
            WHERE Username = ?
        """
        async with self.database.acquire_cursor() as cursor:
            await cursor.execute(query, (username,))
            row = await cursor.fetchone()
            if not row:
                return None

            return UserAccount(
                user_id=int(row[0]),
                username=str(row[1]),
                password_hash=bytes(row[2]),
                role=str(row[3]),
                is_active=bool(row[4]),
                created_at=row[5],
                updated_at=row[6],
                last_login_at=row[7],
            )

    async def update_last_login(self, user_id: int) -> None:
        query = """
            UPDATE [dbo].[UserAccount]
            SET LastLoginAt = SYSUTCDATETIME(),
                UpdatedAt = SYSUTCDATETIME()
            WHERE UserId = ?
        """
        async with self.database.acquire_cursor() as cursor:
            await cursor.execute(query, (user_id,))