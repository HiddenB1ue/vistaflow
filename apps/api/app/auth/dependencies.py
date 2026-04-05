from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.config import auth_settings

bearer_scheme = HTTPBearer()


async def require_admin_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    if not auth_settings.ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin 服务未就绪")
    if credentials.credentials != auth_settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="认证失败")
