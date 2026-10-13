from dataclasses import dataclass
from src.features.Tradebook.Application.DTO.Inputs.BiDirectionalPaginationDTO import BiDirectionalPaginationDTO
from src.features.Tradebook.Application.DTO.Inputs.UserdataDTO import UserDataDTO

@dataclass(frozen=True)
class TradeBookDTO:
    user:UserDataDTO
    pagination:BiDirectionalPaginationDTO