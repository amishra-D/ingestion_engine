import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserAccount:
    user_id: int
    username: str
    password_hash: bytes
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime

    def verify_password(self, plain_password: str) -> bool:
        """Verifies plain password against stored 64-byte SHA-512 binary hash."""
        computed_hash = hashlib.sha512(plain_password.encode("utf-8")).digest()
        return hmac.compare_digest(self.password_hash, computed_hash)

    def can_login(self) -> bool:
        return self.is_active