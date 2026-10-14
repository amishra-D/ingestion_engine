from fastapi import APIRouter, Depends, HTTPException, status
import time
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.features.Tradebook.Application.DTO.Inputs.UserdataDTO import UserDataDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import TradeBookPageOutDto
from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Inputs.BiDirectionalPaginationDTO import BiDirectionalPaginationDTO
from src.features.Tradebook.Application.use_cases.get_trade import GetTradeUseCase
from src.features.Tradebook.Domain.exceptions import TradebookException
from src.features.Tradebook.Infrastructure.repositories.get_trade import (
    GetTradeRepository,
)
from src.shared.database.connection import db
from src.shared.database.sp_executor import StoredProcedureExecutor
from src.shared.security.dependencies import TokenPayload, require_roles

router = APIRouter(prefix="/tradebook", tags=["Tradebook"])


def get_trade_use_case() -> GetTradeUseCase:
    sp_executor = StoredProcedureExecutor(db)
    repository = GetTradeRepository(sp_executor)
    return GetTradeUseCase(repository)


@router.post("/get-tradebook", response_model=TradeBookPageOutDto, status_code=status.HTTP_200_OK)
async def get_tradebook_req(
    user_query: UserRequest,
    current_user: TokenPayload = Depends(require_roles(["ADMIN", "BROKER", "DEALER", "GROUP"])),
    use_case: GetTradeUseCase = Depends(get_trade_use_case),
) -> TradeBookPageOutDto:
    try:
        return await use_case.execute_get_trade(user_query, current_user)
    except TradebookException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
