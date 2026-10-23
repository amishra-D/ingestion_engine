import base64
import binascii


def encode_cursor(cursor_id: int | str | None) -> str | None:
    """Encodes a numeric trade ID into an opaque Base64 cursor string.

    Returns None if cursor_id is None, empty, 0, or non-positive.
    If already a valid Base64 encoded numeric cursor, returns it as-is.
    """
    if cursor_id is None:
        return None

    if isinstance(cursor_id, int):
        if cursor_id <= 0:
            return None
        return base64.b64encode(str(cursor_id).encode("utf-8")).decode("utf-8")

    if isinstance(cursor_id, str):
        val = cursor_id.strip()
        if not val or val == "0":
            return None

        # If it's a numeric string (e.g. from SQL query output '500')
        if val.isdecimal():
            numeric_val = int(val)
            if numeric_val <= 0:
                return None
            return base64.b64encode(val.encode("utf-8")).decode("utf-8")

        # Check if already a valid Base64 encoded positive numeric cursor
        try:
            decoded = base64.b64decode(val, validate=True).decode("utf-8")
            if decoded.isascii() and decoded.isdecimal() and int(decoded) > 0:
                return val
        except Exception:
            pass

        raise ValueError(f"Invalid cursor value to encode: {cursor_id}")

    return None


def decode_cursor(cursor_str: str | int | None) -> int | None:
    """Decodes an incoming Base64 cursor string to a positive integer trade ID.

    Accepts positive integers directly (e.g. for testing/internal calls).
    Converts None, empty string, or whitespace to None.
    Raises ValueError if invalid Base64, non-numeric, or non-positive.
    """

    if cursor_str is None:
        return None

    # If cursor is an integer check if its positive
    if isinstance(cursor_str, int):
        if cursor_str <= 0:
            raise ValueError("Cursor ID must be positive")
        return cursor_str

    # Cursor should be base64 string or an integer
    if not isinstance(cursor_str, str):
        raise ValueError("Cursor must be a Base64 string or integer")

    val = cursor_str.strip()
    if not val:
        return None

    try:
        raw = base64.b64decode(val, validate=True)
        decoded = raw.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid Base64 cursor: {e}") from e

    if not decoded.isascii() or not decoded.isdecimal():
        raise ValueError("Cursor must contain a numeric ID")

    cursor_id = int(decoded)
    if cursor_id <= 0:
        raise ValueError("Cursor ID must be positive")

    return cursor_id
