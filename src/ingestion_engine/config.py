from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class DealerSeed:
    exchange: str
    terminal_id: str
    dealer_name: str
    dealer_code: str
    group_code: str
    account_code: str
    ctcl_id: str


# Strictly matched with sql/seed_query.sql
SEED_DEALERS: Final[list[DealerSeed]] = [
    DealerSeed(
        exchange="NSE",
        terminal_id="TERM001",
        dealer_name="SUP Dealer",
        dealer_code="SUP",
        group_code="HO",
        account_code="90068",
        ctcl_id="CTCL001",
    ),
    DealerSeed(
        exchange="NSE",
        terminal_id="TERM002",
        dealer_name="Dealer One",
        dealer_code="D001",
        group_code="HO",
        account_code="90068",
        ctcl_id="CTCL002",
    ),
    DealerSeed(
        exchange="NSE",
        terminal_id="TERM003",
        dealer_name="Dealer Two",
        dealer_code="D002",
        group_code="HO",
        account_code="90068",
        ctcl_id="CTCL003",
    ),
    DealerSeed(
        exchange="NSE",
        terminal_id="TERM004",
        dealer_name="Dealer Three",
        dealer_code="D003",
        group_code="HO",
        account_code="90069",
        ctcl_id="CTCL004",
    ),
    DealerSeed(
        exchange="NSE",
        terminal_id="TERM005",
        dealer_name="Dealer Four",
        dealer_code="D004",
        group_code="GRP2",
        account_code="90069",
        ctcl_id="CTCL005",
    ),
]

SEED_USERNAMES: Final[list[str]] = ["admin", "SUP", "D001", "broker1"]

# Derivatives market contracts for sample generation
SAMPLE_INSTRUMENTS: Final[list[dict]] = [
    {
        "symbol": "NIFTY",
        "base_strike": 25000,
        "strike_step": 50,
        "lot_size": 25,
        "min_price": 50.0,
        "max_price": 350.0,
    },
    {
        "symbol": "BANKNIFTY",
        "base_strike": 55000,
        "strike_step": 100,
        "lot_size": 15,
        "min_price": 120.0,
        "max_price": 600.0,
    },
    {
        "symbol": "FINNIFTY",
        "base_strike": 24000,
        "strike_step": 50,
        "lot_size": 40,
        "min_price": 40.0,
        "max_price": 280.0,
    },
]

MEMBER_CODE: Final[str] = "MEM001"
ALGO_ID: Final[str] = "ALGO001"
SECURITY_TYPE: Final[str] = "FUTOPT"
REFERENCE_TEXT: Final[str] = "INGESTION"
