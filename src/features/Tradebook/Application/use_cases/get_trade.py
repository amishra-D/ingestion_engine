from src.features.Tradebook.Application.DTO.Inputs.TradeBookDTO import (
    TradeBookDTO,
    UserDataDTO,
)
from src.features.Tradebook.Application.DTO.Outputs.TradeBookOutDto import (
    TradeBookPageOutDto,
)
from src.features.Tradebook.Application.ports.GetTradesRepository import (
    IGetTradesRepository,
)
from src.features.Tradebook.Presentation.schemas.UserRequest import UserRequest
from src.shared.security.dependencies import TokenPayload
from src.features.Tradebook.Domain.policies.TradeBookAccessPolicy import (
    TradeBookAccessPolicy,
)
from src.features.Tradebook.Application.DTO.Inputs.BiDirectionalPaginationDTO import (
    BiDirectionalPaginationDTO,
)


class GetTradeUseCase:
    def __init__(self, repository: IGetTradesRepository):
        self.repository = repository

    async def execute_get_trade(
        self, query: UserRequest, current_user: TokenPayload
    ) -> TradeBookPageOutDto:
        # 1. Enforce Domain RBAC Business Rules
        scope = TradeBookAccessPolicy.resolve_previlege(
            current_role=current_user.role,
            current_id=current_user.sub,
            requested_role=query.role,
            requested_id=query.userid,
            account_code=query.accountcode,
            group_code=query.groupcode,
        )

        # 2. Construct securely bounded TradeBookDTO
        dto = TradeBookDTO(
            user=UserDataDTO(
                role=scope.effective_role,
                userid=scope.effective_user_id,
                accountcode=scope.account_code,
                groupcode=scope.group_code,
            ),
            pagination=BiDirectionalPaginationDTO(
                cursor_start=query.cursor_start,
                cursor_end=query.cursor_end,
                limit=query.limit,
            ),
        )

        # 3. Execute via Repository Port
        return await self.repository.execute_get_trade(dto)
