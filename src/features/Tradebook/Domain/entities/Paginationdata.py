from dataclasses import dataclass


@dataclass
class PaginationData:
    cursor_start: int | None = None
    cursor_end: int | None = None
    has_prev: bool = False
    has_next: bool = False