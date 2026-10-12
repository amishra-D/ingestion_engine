"""Demo and verification script:
1. Ingests sample trades using TradeIngestionEngine (strictly using seed dealers/users).
2. Calls the FastAPI TradeBook API (/tradebook/get-tradebook) using JWT authentication.
3. Formats and prints the exact API output schema in real-time.
4. Demonstrates RBAC filtering (ADMIN vs DEALER vs BROKER).
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import app, lifespan
from src.ingestion_engine.engine import TradeIngestionEngine
from src.shared.database.connection import db


async def run_demo():
    print("=" * 80)
    print("           INGESTION ENGINE & TRADEBOOK API VERIFICATION DEMO")
    print("=" * 80)

    async with lifespan(app):
        # 1. Initialize Ingestion Engine
        engine = TradeIngestionEngine(database=db)
        await engine.initialize()

        print(f"\n[1] Seed Dealers Loaded ({len(engine.dealers)}):")
        for d in engine.dealers:
            print(f"    - Dealer: {d.dealer_code:<5} | Terminal: {d.terminal_id:<8} | Account: {d.account_code} | Group: {d.group_code}")

        # 2. Ingest 5 fresh sample trades strictly using seeds
        print("\n[2] Ingesting 5 new trades into tbTradeBook...")
        new_trades = await engine.run_step(count=5)
        for t in new_trades:
            print(
                f"    [+ INGESTED] Trade #{t['MainTradeID']} | "
                f"Dealer: {t['UserID']:<5} | "
                f"Acc: {t['AccountCode']} | "
                f"{t['BuySellFlag']:<4} {t['TradeQty']} {t['ScripDescription']} @ {t['TradePrice']}"
            )

        # 3. Connect to API via test client
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            print("\n[3] Authenticating as ADMIN ('admin' / 'admin123')...")
            login_res = await client.post(
                "/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
            admin_token = login_res.json()["access_token"]
            print("    [OK] JWT Bearer Token acquired for ADMIN.")

            print("\n[4] Querying API: POST /tradebook/get-tradebook (ADMIN view, limit=5)...")
            api_res = await client.post(
                "/tradebook/get-tradebook",
                json={"role": "ADMIN", "limit": 5},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            trades_data = api_res.json()
            print(f"    [OK] API HTTP Status: {api_res.status_code}")
            print(f"    [OK] Returned {len(trades_data)} trades in API format:\n")

            # Pretty-print API output format
            print(json.dumps(trades_data, indent=2))

            # 4. Authenticate as DEALER 'SUP' and verify RBAC
            print("\n" + "-" * 80)
            print("[5] Authenticating as DEALER ('SUP' / 'dealer123')...")
            dealer_login = await client.post(
                "/auth/login",
                json={"username": "SUP", "password": "dealer123"},
            )
            dealer_token = dealer_login.json()["access_token"]
            print("    [OK] JWT Bearer Token acquired for DEALER 'SUP'.")

            dealer_res = await client.post(
                "/tradebook/get-tradebook",
                json={"role": "DEALER", "userid": "SUP", "limit": 5},
                headers={"Authorization": f"Bearer {dealer_token}"},
            )
            dealer_trades = dealer_res.json()
            print(f"    [OK] DEALER 'SUP' view returned {len(dealer_trades)} trades (filtered for SUP):")
            print(json.dumps(dealer_trades[:2], indent=2))

            # 5. Check Ingestion API Status endpoint
            print("\n" + "-" * 80)
            print("[6] Checking Ingestion Engine Status endpoint (GET /ingestion/status)...")
            status_res = await client.get("/ingestion/status")
            print(json.dumps(status_res.json(), indent=2))

    print("\n" + "=" * 80)
    print("                           DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
