from __future__ import annotations

from app.exceptions import NotFoundError


class TrainNotFound(NotFoundError):
    """指定车次未找到。"""

    def __init__(self, train_code: str) -> None:
        super().__init__(f"未找到车次 {train_code}")
