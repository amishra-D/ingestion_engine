import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
import re
import pytest
import pyodbc
import pathlib

from typing import Generator, AsyncGenerator, Any
from testcontainers.community.mssql import SqlServerContainer

from src.features.Auth.Infrastructure.repositories.LoginRepository import (
    LoginRepository,
)
from src.features.Tradebook.Infrastructure.repositories.get_trade import (
    GetTradeRepository,
)
from src.shared.database.connection import Database
from src.shared.database.sp_executor import StoredProcedureExecutor

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
from src.shared.security.jwt import create_access_token


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
    return create_access_token(username="admin", user_id=1, role="ADMIN")


@pytest.fixture
def dealer_token():
    return create_access_token(username="SUP", user_id=2, role="DEALER")


@pytest.fixture
def broker_token():
    return create_access_token(username="broker1", user_id=4, role="BROKER")


@pytest.fixture
def admin_headers(admin_token: str):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def dealer_headers(dealer_token: str):
    return {"Authorization": f"Bearer {dealer_token}"}


@pytest.fixture
def broker_headers(broker_token: str):
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


## Configurations for integration tests

# Path references
SQL_DIR = pathlib.Path(__file__).parents[2] / "sql"
SCRIPTS_SQL = SQL_DIR / "scripts.sql"
SEED_SQL = SQL_DIR / "seed_query.sql"

TEST_PASSWORD = "StrongIntegrationPassword123"
DB_NAME = "friskit_sample"


def make_odbc_dsn(host: str, port: int, database: str = "master") -> str:
    """Builds an ODBC connection string for Driver 18."""
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={host},{port};DATABASE={database};"
        f"UID=sa;PWD={TEST_PASSWORD};TrustServerCertificate=yes;"
    )


def execute_sql_batches(conn: pyodbc.Connection, raw_script: str) -> None:
    """Splits SQL content on GO boundaries and executes batches safely."""
    cursor = conn.cursor()
    batches = re.split(r"^\s*GO\s*$", raw_script, flags=re.MULTILINE | re.IGNORECASE)
    for batch in batches:
        statement = batch.strip()
        if not statement:
            continue
        try:
            cursor.execute(statement)
        except pyodbc.Error as exc:
            # Skip non-critical database-level tuning options unsupported by Linux container
            if any(
                opt in statement
                for opt in (
                    "FILESTREAM",
                    "COMPATIBILITY_LEVEL",
                    "ACCELERATED_DATABASE_RECOVERY",
                )
            ):
                continue
            raise RuntimeError(f"Failed to execute batch:\n{statement}") from exc
    cursor.close()


@pytest.fixture(scope="session")
def mssql_dsn() -> Generator[str, Any, Any]:
    """
    1. Boots a SQL Server 2025 container.
    2. Reads and sanitizes sql/scripts.sql (UTF-16 encoded, replaces Windows paths).
    3. Executes all DDL (Tables, Views, Procedures).
    4. Executes sql/seed_query.sql for test data.
    5. Yields the final connection string to friskit_sample.
    """
    with SqlServerContainer(
        image="mcr.microsoft.com/mssql/server:2025-latest",
        password=TEST_PASSWORD,
    ) as mssql:
        host = mssql.get_container_host_ip()
        port = mssql.get_exposed_port(1433)

        master_dsn = make_odbc_dsn(host, port, database="master")

        with pyodbc.connect(master_dsn, autocommit=True) as conn:
            # 1. Read scripts.sql with UTF-16 encoding
            raw_scripts = SCRIPTS_SQL.read_text(encoding="utf-16")

            # 2. Sanitize: Replace Windows physical file specification with clean CREATE DATABASE
            sanitized_scripts = re.sub(
                r"CREATE DATABASE\s+\[friskit_sample\][^;]+?GO",
                f"IF DB_ID('{DB_NAME}') IS NULL CREATE DATABASE [{DB_NAME}]\nGO",
                raw_scripts,
                flags=re.DOTALL | re.IGNORECASE,
            )

            # 3. Execute all batches in scripts.sql (creates friskit_sample, tables, view, SP)
            execute_sql_batches(conn, sanitized_scripts)

            # 4. Execute seed_query.sql (UTF-8) to populate test rows
            if SEED_SQL.exists():
                seed_script = SEED_SQL.read_text(encoding="utf-8")
                execute_sql_batches(conn, seed_script)

        # Yield target DSN pointing directly to friskit_sample
        yield make_odbc_dsn(host, port, database=DB_NAME)


@pytest.fixture(scope="session")
async def test_db(mssql_dsn: str) -> AsyncGenerator[Database, None]:
    """
    Async session fixture initializing the aioodbc connection pool
    using the application's Database class.
    """
    db_instance = Database(conn_str=mssql_dsn, min_pool_size=1, max_pool_size=5)
    await db_instance.create_connection()
    yield db_instance
    await db_instance.close_connection()


@pytest.fixture
def login_repo(test_db: Database) -> LoginRepository:
    """Repository fixture wired to the live container database."""
    return LoginRepository(database=test_db)


@pytest.fixture
def trade_repo(test_db: Database) -> GetTradeRepository:
    """Repository fixture wired to the live usp_GetTradeBook procedure."""
    executor = StoredProcedureExecutor(database=test_db)
    return GetTradeRepository(sp_executor=executor)
