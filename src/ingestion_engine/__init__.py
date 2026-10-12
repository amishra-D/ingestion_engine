import sys
from pathlib import Path

_workspace_root = str(Path(__file__).resolve().parent.parent.parent)
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

from src.ingestion_engine.config import SEED_DEALERS, SEED_USERNAMES, DealerSeed
from src.ingestion_engine.engine import TradeIngestionEngine, ingestion_engine
from src.ingestion_engine.main import main

__all__ = [
    "SEED_DEALERS",
    "SEED_USERNAMES",
    "DealerSeed",
    "TradeIngestionEngine",
    "ingestion_engine",
    "main",
]
