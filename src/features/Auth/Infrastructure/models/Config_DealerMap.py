
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.features.Tradebook.Infrastructure.base import Base


class ConfigDealerMap(Base):
    __tablename__ = "Config_DealerMap"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[UUID] = mapped_column("DealerMap_ID", Uuid(as_uuid=True), primary_key=True, nullable=False)
    exchange: Mapped[str] = mapped_column("Exchange", String(12), nullable=False)
    term_id: Mapped[str] = mapped_column("TerminalID", String(30), nullable=False)
    dealer_name: Mapped[str | None] = mapped_column("DealerName", String(50), nullable=True)
    dealer_code: Mapped[str] = mapped_column("DealerCode", String(30), nullable=False)
    last_updated: Mapped[datetime] = mapped_column("LastUpdateTime", DateTime, nullable=False)
    group_code: Mapped[str | None] = mapped_column("GroupCode", String(10), nullable=True)
    account_code: Mapped[str] = mapped_column("AccountCode", String(30), nullable=False)
    is_custodian: Mapped[bool] = mapped_column("IsCustodian", Boolean, nullable=False)
