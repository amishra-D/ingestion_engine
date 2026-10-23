import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    TradeBookOutDto,
)
from src.ingestion_engine.engine import ingestion_engine
from src.shared.security.dependencies import TokenPayload, require_roles

router = APIRouter(prefix="/ingestion", tags=["Ingestion Engine"])

# Holds background task reference
_bg_task: asyncio.Task | None = None


class StartIngestionRequest(BaseModel):
    interval_seconds: float = 1.0
    batch_size: int = 1
    max_trades: int | None = None


class IngestionStatusResponse(BaseModel):
    is_running: bool
    total_inserted: int
    last_trade_id: int
    uptime_seconds: float
    trades_per_second: float
    seed_dealers_count: int
    last_trade: dict[str, Any] | None = None


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_ingestion(
    payload: StartIngestionRequest = StartIngestionRequest(),
    current_user: TokenPayload = Depends(require_roles(["ADMIN"])),
):
    """Starts continuous background trade ingestion into tbTradeBook using seed dealers."""
    global _bg_task

    if ingestion_engine.get_status()["is_running"]:
        return {
            "message": "Ingestion engine is already running",
            "status": ingestion_engine.get_status(),
        }

    await ingestion_engine.initialize()

    # Launch background task
    _bg_task = asyncio.create_task(
        ingestion_engine.start(
            interval_seconds=payload.interval_seconds,
            batch_size=payload.batch_size,
            max_trades=payload.max_trades,
        )
    )

    return {
        "message": "Continuous trade ingestion started",
        "config": {
            "interval_seconds": payload.interval_seconds,
            "batch_size": payload.batch_size,
            "max_trades": payload.max_trades,
        },
    }


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_ingestion(
    current_user: TokenPayload = Depends(require_roles(["ADMIN"])),
):
    """Stops continuous background trade ingestion."""
    global _bg_task
    ingestion_engine.stop()
    if _bg_task and not _bg_task.done():
        _bg_task.cancel()
        _bg_task = None
    return {
        "message": "Continuous trade ingestion stopped",
        "status": ingestion_engine.get_status(),
    }


@router.get("/status", response_model=IngestionStatusResponse)
async def get_status():
    """Returns the current state and performance of the ingestion engine."""
    return ingestion_engine.get_status()


@router.post(
    "/generate-sample",
    response_model=list[TradeBookOutDto],
    status_code=status.HTTP_201_CREATED,
)
async def generate_sample(
    count: int = Query(
        default=1, ge=1, le=100, description="Number of sample trades to generate"
    ),
    current_user: TokenPayload = Depends(require_roles(["ADMIN"])),
):
    """Generates and inserts N sample trades immediately and returns them in the TradeBook API format."""
    await ingestion_engine.initialize()
    trades = await ingestion_engine.run_step(count=count)

    # Return in the exact TradeBook API format
    return [
        TradeBookOutDto(
            trade_id=t["MainTradeID"],
            member_code=str(t["MemberCode"]),
            symbol=t["ScripCode"],
            quantity=t["TradeQty"],
            price=t["TradePrice"],
            trade_time=t["DateTime"],
        )
        for t in trades
    ]
