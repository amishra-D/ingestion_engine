from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class TradeBookOutDto:
    trade_id: int
    member_code: str
    symbol: str
    quantity: int
    price: Decimal
    trade_time: datetime | str


@dataclass(frozen=True)
class PaginationOutDto:
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    has_prev: bool = False
    has_next: bool = False


@dataclass(frozen=True)
class TradeBookPageOutDto:
    data: list[TradeBookOutDto]
    pagination: PaginationOutDto
