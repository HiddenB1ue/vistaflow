# VistaFlow Backend

Python 3.12 + FastAPI + asyncpg 后端服务。

## 快速开始

```bash
cd apps/api

# 安装依赖
uv sync

# 复制环境变量
cp .env.example .env.development
# 编辑 .env.development 填写数据库连接等配置

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

## 开发

```bash
# Lint
uv run ruff check .

# 类型检查
uv run mypy app tests

# 测试
uv run pytest --cov=app --cov-report=term-missing
```

## 架构

见 [ARCHITECTURE.md](./ARCHITECTURE.md)
