
from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import TradeBookPageOutDto
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)


class GetTradeUseCase:
    def __init__(self, repository: IGetTradesRepository):
        self.repository = repository

    async def execute_get_trade(self, user_data: TradeBookDTO) -> TradeBookPageOutDto:
        return await self.repository.execute_get_trade(user_data)