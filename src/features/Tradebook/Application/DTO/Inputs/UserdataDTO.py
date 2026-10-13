from dataclasses import dataclass


@dataclass(frozen=True)
class UserDataDTO:
    role: str = ""
    userid: str = ""
    accountcode: str = ""
    groupcode: str = ""