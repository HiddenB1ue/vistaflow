# VistaFlow Admin

`apps/admin` 是 VistaFlow 的管理端前端，基于 Vite、React 19、TypeScript 和 TanStack Query。

当前主要页面：

- 登录页
- Overview 概览页
- Tasks 任务管理页
- Data 数据管理页
- Config 配置管理页
- Log 日志页

## Directory Structure

```text
apps/admin/
├── src/
│   ├── pages/               # 页面级组件
│   │   ├── OverviewView.tsx # 概览页
│   │   ├── TasksView.tsx    # 任务管理页
│   │   ├── DataView.tsx     # 数据管理页
│   │   ├── ConfigView.tsx   # 配置页
│   │   ├── LogView.tsx      # 日志页
│   │   └── LoginView.tsx    # 登录页
│   ├── components/          # 通用组件、布局和弹层
│   ├── services/            # API 请求、mock 服务与运行时封装
│   ├── stores/              # Zustand 状态管理
│   ├── contexts/            # React 上下文，例如认证上下文
│   ├── hooks/               # 自定义 hooks
│   ├── constants/           # 常量与文案
│   ├── config/              # 前端配置
│   ├── types/               # 前端类型定义
│   ├── utils/               # 工具函数
│   ├── App.tsx              # 路由与应用入口
│   └── main.tsx             # 挂载入口
├── index.html               # Vite 入口 HTML
├── package.json             # 前端脚本与依赖
├── vite.config.ts           # Vite 配置
└── vitest.config.ts         # Vitest 配置
```

## Local Development

从仓库根目录：

```bash
pnpm install
pnpm --filter @vistaflow/admin dev
```

或在当前目录：

```bash
pnpm install
pnpm dev
```

默认地址：`http://localhost:5174`

## Common Commands

```bash
pnpm dev
pnpm build
pnpm test
pnpm preview
```

## Environment Variables

管理端当前使用的环境变量：

- `VITE_API_BASE_URL`：后端接口基础地址，默认会读取 `/api/v1`
- `VITE_USE_MOCK`：是否启用 mock 数据，默认不是 `false` 时会走 mock

推荐本地配置示例：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=false
```

## Authentication

- 登录后令牌会保存在浏览器本地存储中
- 遇到后端 `401` 时会自动清理令牌并跳转回登录页
- 如需联调真实登录，请先启动 `apps/api`

## Shared Workspace Packages

- `@vistaflow/api-client`
- `@vistaflow/design-tokens`
- `@vistaflow/types`
- `@vistaflow/ui`
- `@vistaflow/utils`

## Notes

- 文档以本 README 为主，目录说明和启动方式统一在这里维护
