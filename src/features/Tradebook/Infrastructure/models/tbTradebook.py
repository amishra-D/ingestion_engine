from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.features.Tradebook.Infrastructure.base import Base


class TradeBookModel(Base):
    __tablename__ = "tbTradeBook"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    sql_datetime: Mapped[str] = mapped_column("SQLDateTime", String(80), nullable=False)

    datetime: Mapped[str] = mapped_column("DateTime", String(80), nullable=False)

    trade_num: Mapped[str] = mapped_column("TradeNum", String(80), nullable=False)

    order_num: Mapped[str] = mapped_column("OrderNum", String(80), nullable=False)

    user_id: Mapped[str] = mapped_column("UserID", String(20), nullable=False)

    terminal_id: Mapped[str] = mapped_column("TerminalID", String(20), nullable=False)

    ctcl_id: Mapped[str] = mapped_column("CTCLID", String(20), nullable=False)

    algo_id: Mapped[str] = mapped_column("AlgoID", String(20), nullable=False)

    account_code: Mapped[str] = mapped_column("AccountCode", String(20), nullable=False)

    member_code: Mapped[str] = mapped_column("MemberCode", String(20), nullable=False)

    scrip_code: Mapped[str] = mapped_column("ScripCode", String(20), nullable=False)

    exchange: Mapped[str] = mapped_column("Exchange", String(20), nullable=False)

    opt_type: Mapped[str] = mapped_column("OptType", String(20), nullable=False)

    expiry_date: Mapped[str] = mapped_column("ExpiryDate", String(80), nullable=False)

    strike_price: Mapped[float] = mapped_column(
        "StrikePrice", Numeric(20, 6), nullable=False
    )

    scrip_description: Mapped[str] = mapped_column(
        "ScripDescription", String(80), nullable=False
    )

    buy_sell_flag: Mapped[str] = mapped_column("BuySellFlag", String(4), nullable=False)

    trade_qty: Mapped[int] = mapped_column("TradeQty", Integer, nullable=False)

    trade_price: Mapped[float] = mapped_column(
        "TradePrice", Numeric(20, 6), nullable=False
    )

    main_trade_id: Mapped[int] = mapped_column("MainTradeID", Integer, nullable=False)

    security_type: Mapped[str] = mapped_column(
        "SecurityType", String(20), nullable=False
    )

    reference_text: Mapped[str] = mapped_column(
        "ReferenceText", String(50), nullable=False
    )

    pending_qty: Mapped[int] = mapped_column("PendingQty", Integer, nullable=False)

    custom_id: Mapped[int | None] = mapped_column("CustomID", Integer, nullable=True)
