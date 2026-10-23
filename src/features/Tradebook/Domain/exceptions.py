class TradebookException(Exception):
    """Base domain exception for Tradebook feature."""


class PrivilegeEscalationException(TradebookException):
    """Raised when a user attempts to assume a higher or unauthorized role."""

    def __init__(self, current_role: str, target_role: str):
        super().__init__(
            f"Privilege escalation denied: role '{current_role}' cannot assume role '{target_role}'"
        )


class UnauthorizedUserAccessException(TradebookException):
    """Raised when a user attempts to access trades belonging to another user."""

    def __init__(self, current_user: str, target_user: str):
        super().__init__(
            f"Access denied: user '{current_user}' cannot access trades belonging to '{target_user}'"
        )
