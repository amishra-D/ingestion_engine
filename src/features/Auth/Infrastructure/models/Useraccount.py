from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.features.Tradebook.Infrastructure.base import Base


class User(Base):
    __tablename__ = "UserAccount"
    __table_args__ = {"schema": "dbo"}

    user_id: Mapped[int] = mapped_column(
        "UserId", Integer, primary_key=True, autoincrement=True
    )

    username: Mapped[str] = mapped_column("Username", String(50), nullable=False)

    password_hash: Mapped[str] = mapped_column(
        "PasswordHash", String(64), nullable=False
    )

    role: Mapped[str] = mapped_column("Role", String(20), nullable=False)

    is_active: Mapped[bool] = mapped_column("isActive", Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt",
        DateTime(timezone=False),
        nullable=False,
        server_default=text("SYSUTCDATETIME()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        "UpdatedAt",
        DateTime(timezone=False),
        nullable=False,
        server_default=text("SYSUTCDATETIME()"),
    )

    last_login_at: Mapped[datetime] = mapped_column(
        "LastLoginAt",
        DateTime(timezone=False),
        nullable=False,
        server_default=text("SYSUTCDATETIME()"),
    )
