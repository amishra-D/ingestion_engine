
from dataclasses import dataclass


@dataclass(frozen=True)
class BiDirectionalPaginationDTO:
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    limit: int = 10
