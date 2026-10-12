class AuthException(Exception):
    """Base domain exception for authentication."""


class InvalidCredentialsException(AuthException):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


class InactiveUserException(AuthException):
    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message)
