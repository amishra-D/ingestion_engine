from dataclasses import dataclass
from src.features.Tradebook.Domain.value_objects.cursor import decode_cursor

@dataclass
class BiDirectionalPaginationDTO:
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    limit: int = 10

    def __post_init__(self):
        self.cursor_start = decode_cursor(self.cursor_start)
        self.cursor_end = decode_cursor(self.cursor_end)