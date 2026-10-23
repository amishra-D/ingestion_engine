from dataclasses import dataclass


@dataclass(frozen=True)
class LoginInputDTO:
    username: str
    password: str
