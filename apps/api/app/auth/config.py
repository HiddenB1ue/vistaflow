from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# 手动查找并加载 .env 文件（在创建 Settings 之前）
def _find_and_load_env() -> Path | None:
    """查找并加载 .env 文件"""
    current = Path.cwd()
    
    # 尝试当前目录
    for env_name in [".env.development", ".env.local", ".env"]:
        env_path = current / env_name
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return env_path
    
    # 尝试 apps/api 目录
    api_dir = current / "apps" / "api"
    if api_dir.exists():
        for env_name in [".env.development", ".env.local", ".env"]:
            env_path = api_dir / env_name
            if env_path.exists():
                load_dotenv(env_path, override=True)
                return env_path
    
    return None


# 先加载环境变量
env_file = _find_and_load_env()
if env_file:
    print(f"Loaded env file: {env_file}")
else:
    print("No .env file found")


class AuthSettings(BaseSettings):
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    ADMIN_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 创建实例并从环境变量中读取（如果 pydantic 没有读取到）
auth_settings = AuthSettings()

# 如果 pydantic 没有读取到，手动从 os.environ 读取
if not auth_settings.ADMIN_PASSWORD:
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if admin_password:
        auth_settings.ADMIN_PASSWORD = admin_password
        print(f"Manually loaded ADMIN_PASSWORD from environment")

if not auth_settings.ADMIN_USERNAME or auth_settings.ADMIN_USERNAME == "admin":
    admin_username = os.environ.get("ADMIN_USERNAME", "")
    if admin_username:
        auth_settings.ADMIN_USERNAME = admin_username

if not auth_settings.ADMIN_TOKEN:
    admin_token = os.environ.get("ADMIN_TOKEN", "")
    if admin_token:
        auth_settings.ADMIN_TOKEN = admin_token

# 调试信息
print("=" * 50)
print("AUTH SETTINGS LOADED:")
print(f"ADMIN_USERNAME: {auth_settings.ADMIN_USERNAME}")
print(f"ADMIN_PASSWORD: {'*' * len(auth_settings.ADMIN_PASSWORD) if auth_settings.ADMIN_PASSWORD else '(empty)'}")
print(f"ADMIN_TOKEN: {'*' * len(auth_settings.ADMIN_TOKEN) if auth_settings.ADMIN_TOKEN else '(empty)'}")
print("=" * 50)
