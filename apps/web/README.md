# VistaFlow Web

用户端前端应用，基于 Vite + React + TypeScript。

## 开发

从仓库根目录执行：

```bash
pnpm install
pnpm --filter @vistaflow/web dev
```

或者在当前目录执行：

```bash
pnpm install
pnpm dev
```

## 构建

```bash
pnpm build
```

## 环境变量

复制 `.env.example` 为 `.env.development`，主要配置包括：

- `VITE_API_BASE_URL`
- `VITE_AMAP_KEY`
- `VITE_AMAP_STYLE_ID`
- `VITE_USE_MOCK`
