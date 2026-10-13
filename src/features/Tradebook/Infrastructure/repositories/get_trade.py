from typing import Any

from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookPageOutDto import (
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)
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
        return TradeBookPageOutDto.from_db(result_sets)