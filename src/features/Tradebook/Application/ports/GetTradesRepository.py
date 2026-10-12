from abc import ABC, abstractmethod

from src.features.Tradebook.Application.DTO.Inputs.Userdata import UserData
from src.features.Tradebook.Application.DTO.Outputs.TradeBookdto import TradeBookDto


class IGetTradesRepository(ABC):
    @abstractmethod
    async def execute_get_trade(self,user_data:UserData)->list[TradeBookDto]:
        pass