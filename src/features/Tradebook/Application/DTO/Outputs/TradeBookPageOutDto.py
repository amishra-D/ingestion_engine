from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.features.Tradebook.Domain.value_objects.cursor import encode_cursor


@dataclass
class TradeBookOutDto:
    trade_id: int
    member_code: str
    symbol: str
    quantity: int
    price: Decimal
    trade_time: datetime | str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> TradeBookOutDto:
        return cls(
            trade_id=row["MainTradeID"],
            member_code=str(row["MemberCode"]),
            symbol=row["ScripCode"],
            quantity=row["TradeQty"],
            price=row["TradePrice"],
            trade_time=row["DateTime"],
        )


@dataclass(frozen=True)
class PaginationOutDto:
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    has_prev: bool = False
    has_next: bool = False

    @classmethod
    def from_meta(cls, meta: dict[str, Any]) -> PaginationOutDto:
        return cls(
            cursor_start=encode_cursor(meta.get("StartCursor")),
            cursor_end=encode_cursor(meta.get("EndCursor")),
            has_prev=bool(meta.get("HasPrev", False)),
            has_next=bool(meta.get("HasNext", False)),
        )


@dataclass
class TradeBookPageOutDto:
    data: list[TradeBookOutDto]
    pagination: PaginationOutDto

    @classmethod
    def from_db(cls, results: list[list[dict[str, Any]]]) -> TradeBookPageOutDto:
        raw_trades = results[0] if len(results) > 0 else []
        metadata = results[1][0] if len(results) > 1 and results[1] else {}
        return cls(
            data=[TradeBookOutDto.from_row(row) for row in raw_trades],
            pagination=PaginationOutDto.from_meta(metadata),
        )