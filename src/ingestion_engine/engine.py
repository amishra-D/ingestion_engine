import asyncio
import logging
import random
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from src.ingestion_engine.config import (
    ALGO_ID,
    MEMBER_CODE,
    REFERENCE_TEXT,
    SAMPLE_INSTRUMENTS,
    SECURITY_TYPE,
    SEED_DEALERS,
    DealerSeed,
)
from src.shared.database.connection import Database, db

logger = logging.getLogger("ingestion_engine")


class TradeIngestionEngine:
    """Continuously generates and ingests realistic sample trades into dbo.tbTradeBook.

    Strictly restricts dealers, accounts, terminals, and member codes to the seed data.
    """

    def __init__(self, database: Database = db, dealers: list[DealerSeed] | None = None):
        self.database = database
        self.dealers: list[DealerSeed] = dealers or SEED_DEALERS
        self._is_running: bool = False
        self._task: asyncio.Task | None = None
        self._trade_counter: int = 0
        self._total_inserted: int = 0
        self._last_trade: dict[str, Any] | None = None
        self._start_time: float | None = None

    async def initialize(self) -> None:
        """Initializes database pool (if needed) and syncs trade counter with the DB."""
        if self.database.pool is None:
            await self.database.create_connection()

        # Sync counter from current MAX(MainTradeID)
        async with self.database.acquire_cursor() as cursor:
            await cursor.execute("SELECT COALESCE(MAX(MainTradeID), 0) FROM dbo.tbTradeBook")
            row = await cursor.fetchone()
            current_max = row[0] if row and row[0] is not None else 0
            self._trade_counter = int(current_max)

            # Also verify / sync seed dealers from Config_DealerMap if available
            try:
                await cursor.execute(
                    "SELECT Exchange, TerminalID, DealerName, DealerCode, GroupCode, AccountCode "
                    "FROM dbo.Config_DealerMap"
                )
                rows = await cursor.fetchall()
                if rows:
                    db_dealers = []
                    for r in rows:
                        # Find matching ctcl_id from seeds or fallback to CTCL001
                        seed_match = next((s for s in SEED_DEALERS if s.dealer_code == r[3]), None)
                        ctcl = seed_match.ctcl_id if seed_match else "CTCL001"
                        db_dealers.append(
                            DealerSeed(
                                exchange=r[0],
                                terminal_id=r[1],
                                dealer_name=r[2] or f"Dealer {r[3]}",
                                dealer_code=r[3],
                                group_code=r[4] or "HO",
                                account_code=r[5],
                                ctcl_id=ctcl,
                            )
                        )
                    if db_dealers:
                        self.dealers = db_dealers
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Could not query Config_DealerMap directly, using predefined seeds: {e}")

        logger.info(
            f"Ingestion Engine initialized. Starting TradeID counter at {self._trade_counter + 1} "
            f"with {len(self.dealers)} seed dealers."
        )

    def generate_trade_record(self) -> dict[str, Any]:
        """Generates a single synthetic trade strictly adhering to seed dealers and options schema."""
        self._trade_counter += 1
        trade_id = self._trade_counter

        now = datetime.now(UTC)
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Select a seed dealer
        dealer = random.choice(self.dealers)

        # Select an instrument
        instrument = random.choice(SAMPLE_INSTRUMENTS)
        symbol = instrument["symbol"]
        step = instrument["strike_step"]
        base_strike = instrument["base_strike"]

        # Strike price +/- 5 steps around base
        strike_offset = random.randint(-5, 5) * step
        strike_price = Decimal(base_strike + strike_offset)

        opt_type = random.choice(["CE", "PE"])
        buy_sell = random.choice(["BUY", "SELL"])

        # Quantity is 1-4 lots
        lots = random.randint(1, 4)
        quantity = lots * instrument["lot_size"]

        # Realistic price with 2 decimal precision
        price_val = round(
            random.uniform(instrument["min_price"], instrument["max_price"]),
            2,
        )
        trade_price = Decimal(str(price_val))

        scrip_desc = f"{symbol} {int(strike_price)} {opt_type}"
        trade_num = f"TRD{trade_id:06d}"
        order_num = f"ORD{trade_id:06d}"

        # Current or upcoming monthly expiry
        expiry_date = "2026-10-29"

        return {
            "SQLDateTime": timestamp_str,
            "DateTime": timestamp_str,
            "TradeNum": trade_num,
            "OrderNum": order_num,
            "UserID": dealer.dealer_code,
            "TerminalID": dealer.terminal_id,
            "CTCLID": dealer.ctcl_id,
            "AlgoID": ALGO_ID,
            "AccountCode": dealer.account_code,
            "MemberCode": MEMBER_CODE,
            "ScripCode": symbol,
            "Exchange": dealer.exchange,
            "OptType": opt_type,
            "ExpiryDate": expiry_date,
            "StrikePrice": strike_price,
            "ScripDescription": scrip_desc,
            "BuySellFlag": buy_sell,
            "TradeQty": quantity,
            "TradePrice": trade_price,
            "MainTradeID": trade_id,
            "SecurityType": SECURITY_TYPE,
            "ReferenceText": REFERENCE_TEXT,
            "PendingQty": 0,
            "CustomID": None,
        }

    async def insert_trade(self, trade: dict[str, Any]) -> None:
        """Inserts a single trade into dbo.tbTradeBook."""
        await self.insert_batch([trade])

    async def insert_batch(self, trades: list[dict[str, Any]]) -> int:
        """Inserts a batch of trades into dbo.tbTradeBook."""
        if not trades:
            return 0

        columns = [
            "SQLDateTime",
            "DateTime",
            "TradeNum",
            "OrderNum",
            "UserID",
            "TerminalID",
            "CTCLID",
            "AlgoID",
            "AccountCode",
            "MemberCode",
            "ScripCode",
            "Exchange",
            "OptType",
            "ExpiryDate",
            "StrikePrice",
            "ScripDescription",
            "BuySellFlag",
            "TradeQty",
            "TradePrice",
            "MainTradeID",
            "SecurityType",
            "ReferenceText",
            "PendingQty",
            "CustomID",
        ]

        col_clause = ", ".join(columns)
        param_placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO dbo.tbTradeBook ({col_clause}) VALUES ({param_placeholders})"

        async with self.database.acquire_cursor() as cursor:
            for t in trades:
                vals = [t[col] for col in columns]
                await cursor.execute(sql, vals)

        self._total_inserted += len(trades)
        self._last_trade = trades[-1]
        return len(trades)

    async def run_step(self, count: int = 1) -> list[dict[str, Any]]:
        """Generates and inserts `count` trades immediately."""
        trades = [self.generate_trade_record() for _ in range(count)]
        await self.insert_batch(trades)
        return trades

    async def start(
        self,
        interval_seconds: float = 1.0,
        batch_size: int = 1,
        max_trades: int | None = None,
    ) -> None:
        """Runs the continuous ingestion loop."""
        if self._is_running:
            logger.warning("Ingestion engine is already running.")
            return

        self._is_running = True
        self._start_time = time.time()
        logger.info(
            f"Starting trade ingestion loop: interval={interval_seconds}s, "
            f"batch_size={batch_size}, max_trades={max_trades}"
        )

        try:
            inserted_in_session = 0
            while self._is_running:
                trades = await self.run_step(count=batch_size)
                inserted_in_session += len(trades)

                if max_trades is not None and inserted_in_session >= max_trades:
                    logger.info(f"Reached max_trades limit ({max_trades}). Stopping ingestion.")
                    break

                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Ingestion loop cancelled.")
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stops the continuous ingestion loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Ingestion engine stop requested.")

    def get_status(self) -> dict[str, Any]:
        """Returns the current state and metrics of the ingestion engine."""
        uptime = time.time() - self._start_time if self._start_time and self._is_running else 0.0
        rate = (self._total_inserted / uptime) if uptime > 0 else 0.0
        return {
            "is_running": self._is_running,
            "total_inserted": self._total_inserted,
            "last_trade_id": self._trade_counter,
            "uptime_seconds": round(uptime, 2),
            "trades_per_second": round(rate, 2),
            "seed_dealers_count": len(self.dealers),
            "last_trade": self._last_trade,
        }


# Global singleton instance for shared usage across API and CLI
ingestion_engine = TradeIngestionEngine()
