from dataclasses import dataclass


@dataclass(frozen=True)
class UserData:
    role: str = ""
    userid: str = ""
    accountcode: str = ""
    groupcode: str = ""
    cursorid: int = 0
    limit: int = 50