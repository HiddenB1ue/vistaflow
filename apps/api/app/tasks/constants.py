from __future__ import annotations

from typing import Literal

TaskType = Literal["fetch-station", "geocode", "fetch-status", "price", "cleanup"]
TaskStatus = Literal["running", "pending", "completed", "error", "terminated"]
