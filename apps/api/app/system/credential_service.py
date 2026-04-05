from __future__ import annotations

from datetime import UTC, datetime

from app.system.credential_repository import CredentialRepository
from app.system.schemas import CredentialResponse


def _compute_health(expires_at: datetime | None) -> str:
    if expires_at is not None and expires_at < datetime.now(UTC):
        return "expired"
    return "healthy"


def _compute_masked_key(raw_key: str) -> str:
    if len(raw_key) < 12:
        return "•" * len(raw_key)
    return raw_key[:8] + "••••••••••••••" + raw_key[-4:]


class CredentialService:
    def __init__(self, repo: CredentialRepository) -> None:
        self._repo = repo

    async def list_credentials(self) -> list[CredentialResponse]:
        credentials = await self._repo.find_all()
        return [
            CredentialResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                health=_compute_health(c.expires_at),
                maskedKey=_compute_masked_key(c.raw_key),
                quotaInfo=c.quota_info,
                expiryWarning=(
                    "凭证已过期" if _compute_health(c.expires_at) == "expired" else None
                ),
            )
            for c in credentials
        ]
