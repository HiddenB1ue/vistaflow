# VistaFlow Web

`apps/web` 是 VistaFlow 的用户端前端，基于 Vite、React 19、TypeScript 和 TanStack Query。

当前主要功能：

- 出发地、目的地、日期搜索
- 出行方案结果列表展示
- 方案筛选、排序、分页视图
- 与后端 API 或本地 mock 数据联调

说明：

- 用户端地图区域已经移除，结果页当前以路线列表为主

## Directory Structure

```text
apps/web/
├── public/            # 静态资源
├── src/
│   ├── pages/         # 页面级组件
│   │   ├── SearchPage/    # 搜索页
│   │   └── JourneyPage/   # 方案结果页
│   ├── components/    # 通用组件、布局和弹层
│   ├── animations/    # 动画实现
│   ├── services/      # API 请求、mock 数据与数据映射
│   ├── stores/        # Zustand 状态管理
│   ├── hooks/         # 自定义 hooks
│   ├── constants/     # 文案与常量
│   ├── styles/        # 样式变量与主题样式
│   ├── types/         # 前端类型定义
│   ├── utils/         # 纯工具函数
│   ├── assets/        # 图片等资源
│   ├── config/        # 前端配置
│   ├── App.tsx        # 路由与应用入口
│   └── main.tsx       # 挂载入口
├── .env.example       # 环境变量示例
├── index.html         # Vite 入口 HTML
├── package.json       # 前端脚本与依赖
├── vite.config.ts     # Vite 配置
└── vitest.config.ts   # Vitest 配置
```

## Local Development

从仓库根目录：

```bash
pnpm install
pnpm --filter @vistaflow/web dev
```

或在当前目录：

```bash
pnpm install
pnpm dev
```

默认地址：`http://localhost:5173`

## Common Commands

```bash
pnpm dev
pnpm build
pnpm lint
pnpm test
pnpm preview
```

## Environment Variables

当前前端实际使用的环境变量：

- `VITE_API_BASE_URL`：后端接口基础地址
- `VITE_USE_MOCK`：是否启用 mock 数据，默认不是 `false` 时会走 mock

推荐本地配置示例：

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

## Routes

- `/`：搜索页
- `/journey`：方案结果页

## Shared Workspace Packages

- `@vistaflow/api-client`
- `@vistaflow/design-tokens`
- `@vistaflow/types`
- `@vistaflow/ui`
- `@vistaflow/utils`

## Notes

- 站点数据会在应用初始化阶段预加载
- 文档以本 README 为主，目录说明和启动方式统一在这里维护
