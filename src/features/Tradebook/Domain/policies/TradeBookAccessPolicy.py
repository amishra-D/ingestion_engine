
from dataclasses import dataclass
from src.features.Tradebook.Domain.exceptions import (
    PrivilegeEscalationException,
    UnauthorizedUserAccessException,
)
@dataclass(frozen=True)
class QueryScope:
    effective_role:str
    effective_user_id:str
    group_code:str|None
    account_code:str|None

class TradeBookAccessPolicy:
    @staticmethod
    def resolve_previlege(current_role:str,
                          requested_role:str|None,
                          current_id:str,
                          requested_id:str,
                          account_code:str|None,
                          group_code:str|None,)->QueryScope:
        
        current_role= current_role.upper()
        requested_role=requested_role.upper() if requested_role else current_role

        # User tries to request other role without being an admin
        if current_role != "ADMIN" and requested_role != current_role:
            raise PrivilegeEscalationException(current_role=current_role,
                                               target_role=requested_role)

        # Dealer tried to access other dealer level previlege
        if current_role=="DEALER" and requested_id and requested_id!=current_id:
            raise UnauthorizedUserAccessException(current_user=current_id,
                                                  target_user=requested_id)

        effective_role = requested_role if current_role == "ADMIN" else current_role
        effective_user_id = requested_id if current_role == "ADMIN" else current_id

        return QueryScope(effective_role=effective_role,
                          effective_user_id=effective_user_id,
                          group_code=group_code,
                          account_code=account_code)