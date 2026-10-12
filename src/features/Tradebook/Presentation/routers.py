from fastapi import APIRouter, Depends, HTTPException, status

from src.features.Tradebook.Application.DTO.Inputs.Userdata import UserData
from src.features.Tradebook.Application.DTO.Outputs.TradeBookdto import TradeBookDto
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


@router.post("/get-tradebook", response_model=list[TradeBookDto], status_code=status.HTTP_200_OK)
async def get_tradebook_req(
    user_query: UserData,
    current_user: TokenPayload = Depends(require_roles(["ADMIN", "BROKER", "DEALER", "GROUP"])),
    use_case: GetTradeUseCase = Depends(get_trade_use_case)
):
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

        secured_user_query = UserData(
            role=effective_role,
            userid=effective_userid,
            accountcode=user_query.accountcode,
            groupcode=user_query.groupcode,
            cursorid=user_query.cursorid,
            limit=user_query.limit,
        )

        return await use_case.execute_get_trade(secured_user_query)

    except PrivilegeEscalationException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UnauthorizedUserAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
