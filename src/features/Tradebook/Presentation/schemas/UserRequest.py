from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.features.Tradebook.Domain.value_objects.cursor import decode_cursor


class UserRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str = ""
    userid: str = Field(
        default="", validation_alias=AliasChoices("userid", "user_id", "UserId")
    )
    accountcode: str = Field(
        default="",
        validation_alias=AliasChoices("accountcode", "account_code", "AccountCode"),
    )
    groupcode: str = Field(
        default="",
        validation_alias=AliasChoices("groupcode", "group_code", "GroupCode"),
    )
    cursor_start: str | int | None = None
    cursor_end: str | int | None = None
    limit: int = Field(default=10, ge=10, le=5000)

    @field_validator("cursor_start", "cursor_end", mode="before")
    @classmethod
    def validate_and_decode_cursor(cls, value):
        return decode_cursor(value)

    @model_validator(
        mode="after"
    )  # Checking if only one cursor if provided for either forward or backward pagination
    def validate_cursors(self):
        if self.cursor_start is not None and self.cursor_end is not None:
            raise ValueError("Provide only one cursor per request")
        return self
