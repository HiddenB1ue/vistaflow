# VistaFlow — Claude Code 工作上下文

## 项目是什么

智能出行规划 Web App。用户输入出发地、目的地、日期，获取高铁方案列表，左侧高德地图显示路线，右侧卡片展示方案详情。

完整架构契约在 `ARCHITECTURE.md`，UI 原型在 `prototype/vistaflow-multipage.html`。 **开始任何任务前必须读这两个文件。**

------

## 技术栈（不得更改）

```
React 19 + TypeScript 5（严格模式）
Vite 8
Tailwind CSS 4
Zustand 4（状态管理）
GSAP 3.12（动画，唯一动画库）
TanStack Query 5（数据请求）
React Router 7
高德地图 JS API 2.x
```

------

## 目录结构（严格遵守）

```
src/
├── pages/          # 页面：HomePage / ResultsPage
├── components/     # 纯展示组件，不订阅 Store
│   ├── layout/     # AppLayout Navbar Breadcrumb
│   ├── overlays/   # TransitionOverlay FilterDrawer
│   ├── background/ # AuraBackground NoiseTexture
│   └── map/        # AmapContainer PulseMapOverlay
├── animations/     # 所有 GSAP 调用，不 import React
├── stores/         # searchStore routeStore uiStore
├── services/       # API 层 + mock 数据
├── types/          # route.ts search.ts theme.ts
├── styles/         # tokens.css fonts.css
├── hooks/          # useTheme useTimeGreeting useMouseAura
└── utils/          # duration.ts price.ts seat.ts
```

------

## 铁律（违反直接打回）

**动画**

- 禁止在 `.tsx` 文件中直接调用 `gsap.to()` / `gsap.from()`
- 所有 GSAP 调用封装在 `animations/` 目录，通过 custom hook 暴露
- `animations/` 文件禁止 import React 或任何 Store

**状态**

- `components/` 层禁止订阅 Store（`useSearchStore` 等）
- 数据通过 Props 从 Pages 层向下传递
- Store 之间禁止互相 import

**样式**

- 禁止 hardcode 颜色值，必须用 CSS 变量或 Tailwind 令牌
- 主题切换唯一入口：`useTheme` hook，禁止直接操作 `document.body.classList`
- 主题通过 `html[data-theme="dawn"|"dusk"]` 切换

**类型**

- 禁止使用 `any`
- 组件 Props 必须有具名 interface
- API 响应必须在 `services/` 层转换为 `types/` 中定义的类型后再传给组件

**地图**

- `PulseMapOverlay`（SVG 层）禁止 import 高德 SDK
- 坐标系转换（WGS-84 → GCJ-02）只在 `services/` 层处理

------

## 设计令牌（CSS 变量）

```css
/* dawn 主题（日间，默认） */
--color-bg: #030303
--color-pulse: #E5C07B        /* 品牌金色 */
--color-pulse-rgb: 229, 192, 123
--aura-color-1: #1a2a40
--aura-color-2: rgba(229,192,123,0.15)

/* dusk 主题（夜间） */
--color-pulse: #8B5CF6        /* 品牌紫色 */
--color-pulse-rgb: 139, 92, 246
--aura-color-1: #110e24
--aura-color-2: rgba(139,92,246,0.15)
```

字体：`font-sans`（Inter）/ `font-display`（Space Grotesk）/ `font-serif`（Cormorant Garamond）

------

## 分层职责速查

| 层         | 可以做                                     | 不可以做                            |
| ---------- | ------------------------------------------ | ----------------------------------- |
| Pages      | 调用 Store、调用 Query、组合 Components    | 直接调用 gsap、直接调用 axios       |
| Components | 接收 Props、local useState、调用通用 hooks | 订阅 Store、调用 gsap、发 HTTP 请求 |
| Animations | 接收 DOM ref、返回 GSAP Timeline           | import React、import Store          |
| Services   | HTTP 请求、类型转换                        | UI 逻辑、操作 Store                 |

------

## 页面跳转规则

所有页面跳转必须经过幕布动画，不得裸调 `navigate()`。 跳转通过 `usePageTransition` hook 触发，时序：

```
triggerCurtain('up') → 动画完成 → navigate() → 新页面挂载 → triggerCurtain('down')
```

------

## 当前状态

- 原型：完成（见 `prototype/vistaflow-multipage.html`）
- 工程：待初始化
- 数据接口：未就绪，使用 `services/mock/routes.mock.ts`
- 环境变量：需配置 `VITE_AMAP_KEY` 和 `VITE_AMAP_STYLE_ID`

------

## 每次任务开始前

1. 读 `ARCHITECTURE.md` 确认完整约定
2. 读 `prototype/vistaflow-multipage.html` 确认 UI 行为
3. 确认改动不违反本文件的铁律
4. 有歧义先问，不要自行假设