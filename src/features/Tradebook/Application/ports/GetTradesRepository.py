from abc import ABC, abstractmethod

from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import TradeBookPageOutDto


class IGetTradesRepository(ABC):
    """Port for the get trade repository which is the contract 
                for the repository in the Infrastructure layer"""

    @abstractmethod
    async def execute_get_trade(self, user_data: TradeBookDTO) -> TradeBookPageOutDto:
        pass