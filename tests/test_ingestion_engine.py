import unittest
from unittest.mock import MagicMock

from src.ingestion_engine.config import SEED_DEALERS
from src.ingestion_engine.engine import TradeIngestionEngine


class TestTradeIngestionEngine(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = TradeIngestionEngine(database=self.mock_db)

    def test_only_seed_dealers_used_in_generated_trades(self):
        """Ensures 100 generated trades strictly only use seed dealers, terminals, and accounts."""
        seed_dealer_codes = {d.dealer_code for d in SEED_DEALERS}
        seed_terminals = {d.terminal_id for d in SEED_DEALERS}
        seed_accounts = {d.account_code for d in SEED_DEALERS}

        for _ in range(100):
            trade = self.engine.generate_trade_record()

            # Verify Dealer / UserID
            self.assertIn(trade["UserID"], seed_dealer_codes)
            # Verify Terminal
            self.assertIn(trade["TerminalID"], seed_terminals)
            # Verify Account Code
            self.assertIn(trade["AccountCode"], seed_accounts)
            # Verify Exchange
            self.assertEqual(trade["Exchange"], "NSE")
            # Verify MemberCode
            self.assertEqual(trade["MemberCode"], "MEM001")
            # Verify Option types and Buy/Sell
            self.assertIn(trade["OptType"], ["CE", "PE"])
            self.assertIn(trade["BuySellFlag"], ["BUY", "SELL"])
            self.assertGreater(trade["TradeQty"], 0)
            self.assertGreater(trade["TradePrice"], 0)

    def test_trade_id_increments_monotonically(self):
        self.engine._trade_counter = 10
        t1 = self.engine.generate_trade_record()
        t2 = self.engine.generate_trade_record()
        self.assertEqual(t1["MainTradeID"], 11)
        self.assertEqual(t2["MainTradeID"], 12)
        self.assertEqual(t1["TradeNum"], "TRD000011")
        self.assertEqual(t2["TradeNum"], "TRD000012")

    def test_status_reporting(self):
        status = self.engine.get_status()
        self.assertFalse(status["is_running"])
        self.assertEqual(status["total_inserted"], 0)
        self.assertEqual(status["seed_dealers_count"], 5)


if __name__ == "__main__":
    unittest.main()
