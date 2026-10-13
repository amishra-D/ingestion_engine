from typing import Any

from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    PaginationOutDto,
    TradeBookOutDto,
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)
from src.features.Tradebook.Domain.entities.Paginationdata import PaginationData
from src.shared.database.sp_executor import StoredProcedureExecutor


class GetTradeRepository(IGetTradesRepository):

    def __init__(self, sp_executor: StoredProcedureExecutor):
        self.sp_executor = sp_executor

    async def execute_get_trade(self, user_data: TradeBookDTO) -> TradeBookPageOutDto:
        params: dict[str, Any] = {
            "Role": user_data.user.role,
            "UserId": user_data.user.userid or None,
            "AccountCode": user_data.user.accountcode or None,
            "GroupCode": user_data.user.groupcode or None,
            "StartCursor": user_data.pagination.cursor_start,
            "EndCursor": user_data.pagination.cursor_end,
            "Limit": user_data.pagination.limit,
        }

        result_sets = await self.sp_executor.execute_result_sets("usp_GetTradeBook", params)
        raw_trades = result_sets[0] if len(result_sets) > 0 else []
        raw_meta = result_sets[1][0] if len(result_sets) > 1 and result_sets[1] else {}

        if not raw_trades:
            return TradeBookPageOutDto(
                data=[],
                pagination=PaginationOutDto(
                    cursor_start=None,
                    cursor_end=None,
                    has_prev=False,
                    has_next=False,
                ),
            )

        trades = [
            TradeBookOutDto(
                trade_id=row["MainTradeID"],
                member_code=str(row["MemberCode"]),
                symbol=row["ScripCode"],
                quantity=row["TradeQty"],
                price=row["TradePrice"],
                trade_time=row["DateTime"],
            )
            for row in raw_trades
        ]

        pagination_entity = PaginationData(
            cursor_start=raw_meta.get("StartCursor"),
            cursor_end=raw_meta.get("EndCursor"),
            has_prev=bool(raw_meta.get("HasPrev", False)),
            has_next=bool(raw_meta.get("HasNext", False)),
        )
        pagination = PaginationOutDto(
            cursor_start=pagination_entity.cursor_start,
            cursor_end=pagination_entity.cursor_end,
            has_prev=pagination_entity.has_prev,
            has_next=pagination_entity.has_next,
        )

        return TradeBookPageOutDto(
            data=trades,
            pagination=pagination,
        )