from __future__ import annotations


class BusinessError(Exception):
    """业务层异常，携带 HTTP 状态码和用户友好的错误信息。"""

    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status


class NotFoundError(BusinessError):
    def __init__(self, message: str) -> None:
        super().__init__(message, http_status=404)


class ExternalServiceError(BusinessError):
    def __init__(self, message: str) -> None:
        super().__init__(message, http_status=503)
