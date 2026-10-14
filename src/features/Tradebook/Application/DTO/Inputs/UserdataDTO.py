from dataclasses import dataclass

@dataclass(frozen=True)
class UserDataDTO:
    role: str = ""
    userid: str| None = ""
    accountcode: str|None = ""
    groupcode: str|None = ""