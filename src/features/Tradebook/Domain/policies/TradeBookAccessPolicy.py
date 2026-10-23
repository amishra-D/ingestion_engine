
from dataclasses import dataclass
from src.features.Tradebook.Domain.exceptions import (
    PrivilegeEscalationException,
    UnauthorizedUserAccessException,
)
@dataclass(frozen=True)
class QueryScope:
    effective_role: str
    effective_user_id: str | None
    group_code: str | None
    account_code: str | None

class TradeBookAccessPolicy:
    @staticmethod
    def resolve_previlege(
        current_role: str,
        requested_role: str | None,
        current_id: str,
        requested_id: str | None,
        account_code: str | None,
        group_code: str | None,
    ) -> QueryScope:
        current_role = current_role.upper()
        requested_role = requested_role.upper() if requested_role else current_role

        # User tries to request other role without being an admin
        if current_role != "ADMIN" and requested_role != current_role:
            raise PrivilegeEscalationException(
                current_role=current_role,
                target_role=requested_role,
            )

        # Dealer tried to access other dealer level privilege
        if current_role == "DEALER" and requested_id and requested_id != current_id:
            raise UnauthorizedUserAccessException(
                current_user=current_id,
                target_user=requested_id,
            )

        effective_role = requested_role if current_role == "ADMIN" else current_role

        # Resolve effective_user_id:
        # - DEALER: locked strictly to current_id (dealer's own user code)
        # - ADMIN: can filter by requested_id or view all (None)
        # - BROKER / GROUP: can filter by requested_id (specific dealer) or view all dealers (None)
        if current_role == "DEALER":
            effective_user_id = current_id
        else:
            effective_user_id = requested_id if requested_id else None

        effective_account_code = account_code if account_code else None
        effective_group_code = group_code if group_code else None

        return QueryScope(
            effective_role=effective_role,
            effective_user_id=effective_user_id,
            group_code=effective_group_code,
            account_code=effective_account_code,
        )