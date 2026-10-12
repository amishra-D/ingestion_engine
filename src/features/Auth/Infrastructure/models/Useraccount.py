from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.features.Tradebook.Infrastructure.base import Base


class UserAccountModel(Base):
    __tablename__ = "UserAccount"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column("UserId", Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("Username", String(50), unique=True, nullable=False)
    password_hash: Mapped[bytes] = mapped_column("PasswordHash", LargeBinary(64), nullable=False)
    role: Mapped[str] = mapped_column("Role", String(20), default="DEALER", nullable=False)
    is_active: Mapped[bool] = mapped_column("isActive", Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, server_default=func.sysutcdatetime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime, server_default=func.sysutcdatetime(), nullable=False)
    last_login_at: Mapped[datetime] = mapped_column("LastLoginAt", DateTime, server_default=func.sysutcdatetime(), nullable=False)