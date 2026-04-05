from __future__ import annotations

from app.exceptions import BusinessError


class AuthenticationError(BusinessError):
    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message, http_status=401)
