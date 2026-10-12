
from src.features.Tradebook.Application.DTO.Inputs.Userdata import UserData
from src.features.Tradebook.Application.DTO.Outputs.TradeBookdto import TradeBookDto
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository
)


class GetTradeUseCase:
    def __init__(self,repository:IGetTradesRepository):
        self.repository=repository

    async def execute_get_trade(self,user_data:UserData)->list[TradeBookDto]:
        return await self.repository.execute_get_trade(user_data)