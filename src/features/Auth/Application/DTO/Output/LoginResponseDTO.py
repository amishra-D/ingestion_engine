from dataclasses import dataclass


@dataclass(frozen=True)
class LoginResponseDTO:
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
