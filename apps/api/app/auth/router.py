from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.auth.config import auth_settings
from app.auth.schemas import LoginRequest, LoginResponse
from app.schemas import APIResponse

router = APIRouter(tags=["auth"])


def _generate_and_save_token() -> str:
    """生成新的 token 并保存到 .env 文件"""
    new_token = secrets.token_urlsafe(32)
    
    # 查找 .env 文件
    env_files = [".env.development", ".env.local", ".env"]
    env_path = None
    
    for env_file in env_files:
        path = Path(env_file)
        if path.exists():
            env_path = path
            break
    
    if not env_path:
        # 如果没有找到，创建 .env.development
        env_path = Path(".env.development")
    
    # 读取现有内容
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
    else:
        lines = []
    
    # 更新或添加 ADMIN_TOKEN
    token_found = False
    for i, line in enumerate(lines):
        if line.startswith("ADMIN_TOKEN="):
            lines[i] = f"ADMIN_TOKEN={new_token}"
            token_found = True
            break
    
    if not token_found:
        # 添加到文件末尾
        if lines and not lines[-1].strip():
            lines[-1] = f"ADMIN_TOKEN={new_token}"
        else:
            lines.append(f"ADMIN_TOKEN={new_token}")
    
    # 写回文件
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    return new_token


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(payload: LoginRequest) -> APIResponse[LoginResponse]:
    """管理员登录接口"""
    # 调试信息
    print(f"DEBUG: ADMIN_USERNAME={auth_settings.ADMIN_USERNAME}")
    print(f"DEBUG: ADMIN_PASSWORD={'*' * len(auth_settings.ADMIN_PASSWORD) if auth_settings.ADMIN_PASSWORD else '(empty)'}")
    print(f"DEBUG: Received username={payload.username}")
    
    if not auth_settings.ADMIN_USERNAME or not auth_settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="认证服务未配置")

    if (
        payload.username != auth_settings.ADMIN_USERNAME
        or payload.password != auth_settings.ADMIN_PASSWORD
    ):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 每次登录都生成新的 token
    token = _generate_and_save_token()
    # 更新内存中的配置
    auth_settings.ADMIN_TOKEN = token

    return APIResponse.ok(LoginResponse(token=token))

