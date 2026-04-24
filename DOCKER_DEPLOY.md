# Docker 部署与 GitHub Actions 自动构建镜像

## 概念说明

### 两种部署方式

**方式一：本地构建**
用户 clone 代码后，`docker compose up` 在本地把代码构建成镜像再运行。适合开发阶段。

**方式二：预构建镜像（本项目采用）**
维护者通过 GitHub Actions 把镜像构建好，推送到镜像仓库（ghcr.io）。用户直接拉取现成镜像运行，不需要本地构建环境。

---

## 项目结构

```
├── apps/api/Dockerfile          # API 镜像构建文件
├── docker/
│   ├── Dockerfile.web           # 前端镜像构建文件（web + admin）
│   └── nginx/nginx.conf         # nginx 配置
├── docker-compose.yml           # 用户部署用（拉取预构建镜像）
├── docker-compose.dev.yml       # 开发用（本地构建）
├── .env.example                 # 环境变量模板
└── .github/workflows/
    └── docker-publish.yml       # GitHub Actions 自动构建配置
```

---

## 文件说明

### 1. `apps/api/Dockerfile`

API 是一个持续运行的 Python 进程，需要独立的运行环境。

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY app/ ./app/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. `docker/Dockerfile.web`

前端（web + admin）是静态文件，用多阶段构建：
- **构建阶段**：用 Node 安装依赖、构建共享包、用 vite build 打包
- **运行阶段**：用 nginx 服务静态文件，Node 环境不进入最终镜像

```dockerfile
FROM node:20-alpine AS builder
# ... 安装依赖、构建
FROM nginx:alpine
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html/web
COPY --from=builder /app/apps/admin/dist /usr/share/nginx/html/admin
```

> API 需要 Dockerfile 是因为它是持续运行的进程；web/admin 构建完是静态文件，只需要 nginx 服务。

### 3. `docker/nginx/nginx.conf`

两个 server block：
- 端口 **80**：用户端，`/api/` 反代到 API 容器，`/` 服务 web 静态文件
- 端口 **8080**：管理端，同样反代 API，`/` 服务 admin 静态文件

### 4. `docker-compose.yml`（用户部署版）

直接使用 ghcr.io 上的预构建镜像，5 个服务：

| 服务 | 镜像来源 | 说明 |
|---|---|---|
| postgres | Docker Hub 官方镜像 | 数据库 |
| redis | Docker Hub 官方镜像 | 缓存 |
| api | ghcr.io 预构建 | FastAPI 后端 |
| worker | ghcr.io 预构建（同 api） | 任务队列 worker，启动命令不同 |
| web | ghcr.io 预构建 | nginx 服务前端 |

worker 和 api 用同一个镜像，区别只在启动命令：
```yaml
worker:
  image: ghcr.io/hiddenb1ue/vistaflow-api:latest
  command: ["uv", "run", "python", "-m", "app.tasks.worker"]  # 覆盖默认 CMD
```

### 5. `.github/workflows/docker-publish.yml`

GitHub Actions 配置，触发条件：push 到 main/master 分支或打 tag。

两个 job 并行执行：
- `build-api`：构建 API 镜像 → 推送到 `ghcr.io/hiddenb1ue/vistaflow-api`
- `build-web`：构建前端镜像 → 推送到 `ghcr.io/hiddenb1ue/vistaflow-web`

---

## GitHub Actions 自动构建原理

1. 代码推送到 GitHub
2. GitHub 检测到 `.github/workflows/` 下有 YAML 文件
3. 读取 `on:` 字段判断是否触发（push 到指定分支时触发）
4. 在 GitHub 云服务器上启动 Ubuntu 虚拟机
5. 按 `steps:` 顺序执行：checkout → 登录 ghcr.io → 构建镜像 → 推送

关键：`GITHUB_TOKEN` 是 GitHub 自动提供的临时令牌，不需要手动创建，用于推送镜像到 ghcr.io（GitHub Container Registry）。

---

## 必要配置（只有一步）

GitHub 仓库 → **Settings → Actions → General → Workflow permissions**

选择 **Read and write permissions**，让 `GITHUB_TOKEN` 有写入 Packages 的权限。

---

## 用户部署流程

```bash
git clone https://github.com/HiddenB1ue/vistaflow.git
cd vistaflow
cp .env.example .env
# 编辑 .env，设置 ADMIN_PASSWORD
docker compose up -d
```

访问：
- 用户端：`http://localhost`
- 管理端：`http://localhost:8080`

查看容器状态：
```bash
docker compose ps
docker compose logs api    # 查看 API 日志
docker compose logs worker # 查看 worker 日志
```

---

## 开发时本地构建

```bash
docker compose -f docker-compose.dev.yml up -d
```

---

## 镜像 tag 规则

| 触发条件 | 生成的 tag |
|---|---|
| push 到 main/master | `latest`、`main`、`<commit sha>` |
| 打 tag `v1.2.3` | `1.2.3`、`latest`、`<commit sha>` |
