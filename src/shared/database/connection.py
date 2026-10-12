from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aioodbc
from aioodbc import Connection, Cursor, Pool

from src.shared.config.settings import settings


class Database:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        self.pool: Pool | None = None

    async def create_connection(self) -> None:
        """Initializes the aioodbc connection pool."""
        if self.pool is None:
            self.pool = await aioodbc.create_pool(
                dsn=self.conn_str,
                minsize=5,
                maxsize=20,
                autocommit=True
            )

    async def close_connection(self) -> None:
        """Closes all connections in the pool."""
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    def get_pool(self) -> Pool:
        """Returns the raw connection pool."""
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized")
        return self.pool

    @asynccontextmanager
    async def acquire_connection(self) -> AsyncGenerator[Connection]:
        """Safely acquires a connection from the pool and releases it on exit."""
        pool = self.get_pool()
        async with pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def acquire_cursor(self) -> AsyncGenerator[Cursor]:
        """Safely acquires a connection and cursor from the pool and releases them on exit."""
        async with self.acquire_connection() as conn, conn.cursor() as cursor:
            yield cursor


db = Database(settings.DATABASE_URI)