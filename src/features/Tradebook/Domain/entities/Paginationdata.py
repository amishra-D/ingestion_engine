from dataclasses import dataclass

from src.features.Tradebook.Domain.value_objects.cursor import encode_cursor


@dataclass
class PaginationData:
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    has_prev: bool = False
    has_next: bool = False

    def __post_init__(self):
        self.cursor_start = encode_cursor(self.cursor_start)
        self.cursor_end = encode_cursor(self.cursor_end)