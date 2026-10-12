import argparse
import asyncio
import json
import logging
import signal
import sys

from src.ingestion_engine.engine import TradeIngestionEngine
from src.shared.database.connection import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingestion_engine")


async def async_main(args: argparse.Namespace) -> None:
    engine = TradeIngestionEngine(database=db)

    print("=" * 70)
    print("  Ingestion Engine - Continuous Seed Trade Ingestion & API Output")
    print("=" * 70)
    print(f" Interval       : {args.interval}s")
    print(f" Batch Size     : {args.batch_size} trade(s) per tick")
    print(f" Target Limit   : {args.count or 'Infinite (press Ctrl+C to stop)'}")
    print(f" Allowed Dealers: {[d.dealer_code for d in engine.dealers]}")
    print(" Allowed Users  : ['admin', 'SUP', 'D001', 'broker1']")
    print("-" * 70)

    await engine.initialize()

    stop_event = asyncio.Event()

    def handle_signal():
        print("\n[!] Received stop signal, shutting down gracefully...")
        engine.stop()
        stop_event.set()

    # Setup signal handler for graceful shutdown
    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGINT, handle_signal)
    except NotImplementedError:
        # Windows compatibility for signal handlers
        pass

    inserted_count = 0

    try:
        while not stop_event.is_set():
            trades = await engine.run_step(count=args.batch_size)
            inserted_count += len(trades)

            for trade in trades:
                # Format exactly as the TradeBook API outputs
                api_format_output = {
                    "trade_id": trade["MainTradeID"],
                    "member_code": trade["MemberCode"],
                    "symbol": trade["ScripCode"],
                    "quantity": trade["TradeQty"],
                    "price": str(trade["TradePrice"]),
                    "trade_time": trade["DateTime"],
                }

                print(
                    f"[INGESTED] Trade #{trade['MainTradeID']} | "
                    f"Dealer: {trade['UserID']:<5} | "
                    f"Acc: {trade['AccountCode']} | "
                    f"Term: {trade['TerminalID']} | "
                    f"{trade['BuySellFlag']:<4} {trade['TradeQty']} {trade['ScripDescription']} @ {trade['TradePrice']} | "
                    f"Time: {trade['DateTime']}"
                )

                if args.show_api_format:
                    print("  --> API Response Format:")
                    print("     ", json.dumps(api_format_output, indent=2).replace("\n", "\n      "))

            if args.count and inserted_count >= args.count:
                print(f"\n[OK] Reached target count of {args.count} trades.")
                break

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=args.interval)
            except TimeoutError:
                pass

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n[!] Stopping ingestion...")
    finally:
        status = engine.get_status()
        print("-" * 70)
        print(f"[SUMMARY] Total trades inserted: {inserted_count}")
        print(f"[SUMMARY] Final Trade ID: {status['last_trade_id']}")
        await db.close_connection()
        print("[OK] Database connection closed. Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Continuously ingests realistic seed trades into tbTradeBook."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between trade batches (default: 1.0)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of trades to insert per interval (default: 1)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Total number of trades to insert before stopping (default: run indefinitely)",
    )
    parser.add_argument(
        "--show-api-format",
        action="store_true",
        help="Print the exact JSON structure that the TradeBook API produces",
    )

    args = parser.parse_args()

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
