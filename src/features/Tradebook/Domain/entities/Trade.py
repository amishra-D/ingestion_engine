from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Trade:
    trade_id: int
    member_code: str
    symbol: str
    quantity: int
    price: Decimal
    trade_time: datetime | str