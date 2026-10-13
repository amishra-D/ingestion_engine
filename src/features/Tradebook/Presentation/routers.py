from fastapi import APIRouter, Depends, HTTPException, status
import time
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.features.Tradebook.Application.DTO.Inputs.UserdataDTO import UserDataDTO
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import TradeBookPageOutDto
from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import TradeBookDTO
from src.features.Tradebook.Application.DTO.Inputs.BiDirectionalPaginationDTO import BiDirectionalPaginationDTO
from src.features.Tradebook.Application.use_cases.get_trade import GetTradeUseCase
from src.features.Tradebook.Domain.exceptions import (
    PrivilegeEscalationException,
    UnauthorizedUserAccessException,
)
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
        # 1. Enforce RBAC privilege validation: Non-admin users cannot assume higher or different roles
        if (
            user_query.role
            and user_query.role.upper() != current_user.role.upper()
            and current_user.role.upper() != "ADMIN"
        ):
            raise PrivilegeEscalationException(
                current_role=current_user.role,
                target_role=user_query.role,
            )

        # 2. Dealers cannot query trades belonging to another dealer/user
        if (
            current_user.role.upper() == "DEALER"
            and user_query.userid
            and user_query.userid.upper() != current_user.sub.upper()
        ):
            raise UnauthorizedUserAccessException(
                current_user=current_user.sub,
                target_user=user_query.userid,
            )

        # 3. Construct securely bounded query for the Stored Procedure
        effective_role = user_query.role if current_user.role.upper() == "ADMIN" and user_query.role else current_user.role
        effective_userid = user_query.userid if current_user.role.upper() == "ADMIN" else current_user.sub
        start=time.perf_counter() ### Counter start for tradebook SP execution with DTOs and other overhead
        secured_user_query = TradeBookDTO(
            user=UserDataDTO(role=effective_role,
                            userid=effective_userid,
                            accountcode=user_query.accountcode,
                            groupcode=user_query.groupcode),
            pagination=BiDirectionalPaginationDTO(cursor_start=user_query.cursor_start,
                                                  limit=user_query.limit,
                                                  cursor_end=user_query.cursor_end
                                                  )
            )
        res=await use_case.execute_get_trade(secured_user_query)
        end_time=time.perf_counter()-start
        print(f"The query took {end_time} s") ### Counter end for tradebook SP execution with DTOs and other overhead
        return res

    except PrivilegeEscalationException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UnauthorizedUserAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
