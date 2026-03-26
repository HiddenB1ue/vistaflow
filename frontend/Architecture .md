# VistaFlow 前端架构契约与蓝图

> **文档版本** v1.0  
> **状态** 生效中  
> **适用范围** VistaFlow 前端工程全体成员  
> **原型基准** vistaflow-multipage.html（含 HomePage、ResultsPage 两个视图）

---

## 目录

1. [架构哲学](#1-架构哲学)
2. [技术选型决策表](#2-技术选型决策表)
3. [工程目录结构](#3-工程目录结构)
4. [分层架构与职责边界](#4-分层架构与职责边界)
5. [设计令牌系统](#5-设计令牌系统)
6. [组件规范](#6-组件规范)
7. [状态管理契约](#7-状态管理契约)
8. [动画系统契约](#8-动画系统契约)
9. [地图集成规范](#9-地图集成规范)
10. [数据层规范](#10-数据层规范)
11. [路由规范](#11-路由规范)
12. [工程规范与质量门禁](#12-工程规范与质量门禁)
13. [扩展性约定](#13-扩展性约定)
14. [禁止事项清单](#14-禁止事项清单)

---

## 1. 架构哲学

本项目的三条核心原则，所有技术决策必须服从这三条：

**原则一：视觉个性高于组件复用**
VistaFlow 拥有极强的品牌设计语言（暗色系、Cormorant Garamond 字体、GSAP 剧场动画）。当引入外部组件库与设计风格发生冲突时，优先保护设计语言，用自定义组件替代。

**原则二：动画逻辑与 UI 逻辑必须分离**
GSAP 的命令式写法与 React 的声明式渲染模型存在本质冲突。任何 `gsap.to()` 调用不得出现在组件 JSX 或事件处理函数中，必须封装在 `/animations` 层，通过 custom hook 暴露给组件。

**原则三：以数据契约驱动组件边界**
组件只消费类型化的数据，不直接处理原始 API 响应。所有接口数据在进入组件前，必须经过 `/services` 层的转换和 TypeScript 类型约束。

---

## 2. 技术选型决策表

| 类别 | 选型 | 版本 | 决策理由 | 替代品及放弃原因 |
|------|------|------|----------|------------------|
| 框架 | React | 19.x | Hooks + Ref 模型与 GSAP 协作成熟 | Vue 3：GSAP 集成社区案例少，原型适配成本高 |
| 语言 | TypeScript | 5.x | 严格类型保护路线数据结构 | JavaScript：原型已有复杂数据结构，无类型易出错 |
| 构建 | Vite | 8.x | 冷启动快，HMR 对 GSAP 友好 | CRA：已废弃；Next.js：SSR 对本项目无收益 |
| 路由 | React Router | 7.x | 声明式路由，Outlet 支持全局 Layout | TanStack Router：过于新，生态不够稳定 |
| 样式 | Tailwind CSS | 4.x | 原型已全量使用，直接迁移 | CSS Modules：与原型差异大；Emotion：运行时开销 |
| 状态 | Zustand | 4.x | 轻量无 boilerplate，store 按需订阅 | Redux Toolkit：过重；Jotai：atom 模型不直观 |
| 动画 | GSAP | 3.12.x | 原型核心动画库，幕布转场依赖它 | Framer Motion：spring 动效可作补充，不替代 |
| 数据请求 | TanStack Query | 5.x | 缓存、loading 态、错误重试一体化 | SWR：功能子集；axios 裸用：需手写缓存 |
| 地图 | 高德 JS API | 2.x | 国内合规，自定义样式平台成熟 | Mapbox：需 VPN；MapLibre：无测绘资质风险 |
| 组件底层 | Radix UI Primitives | 1.x | 无样式，仅提供行为和无障碍能力 | Ant Design / MUI：默认样式与 VistaFlow 冲突剧烈 |
| HTTP | Axios | 1.x | 拦截器统一处理 token 和错误码 | fetch：需手写所有错误处理逻辑 |
| 测试 | Vitest + Testing Library | — | 与 Vite 生态一体，配置零成本 | Jest：需额外配置 ESM 转换 |

---

## 3. 工程目录结构

```
vistaflow/
├── public/
│   └── fonts/                        # 自托管字体（避免 Google Fonts 被墙）
│       ├── CormorantGaramond/
│       ├── SpaceGrotesk/
│       └── Inter/
│
├── src/
│   │
│   ├── main.tsx                       # 应用入口，挂载 QueryClient、Router
│   ├── App.tsx                        # 路由出口，全局 Layout 包裹
│   │
│   ├── pages/                         # 页面级组件，与路由一一对应
│   │   ├── HomePage/
│   │   │   ├── index.tsx              # 页面出口
│   │   │   ├── HomeHero.tsx           # 标题区（时间问候语 + 主 Slogan）
│   │   │   ├── NLSearchForm.tsx       # 自然语言搜索表单（三个内联输入框）
│   │   │   └── hooks/
│   │   │       └── useHomeReveal.ts   # 首页入场动画 hook
│   │   │
│   │   └── ResultsPage/
│   │       ├── index.tsx              # 页面出口，负责布局框架
│   │       ├── RouteList.tsx          # 右侧方案列表容器（排序、过滤逻辑）
│   │       ├── RouteCard.tsx          # 单张方案卡片（可展开）
│   │       ├── SegmentTimeline.tsx    # 行程分段时间轴（含换乘节点）
│   │       ├── StopsPanel.tsx         # 可折叠经停站面板
│   │       ├── SeatBadge.tsx          # 席别 + 余票状态徽章
│   │       ├── MapPanel.tsx           # 左侧地图区域容器
│   │       └── hooks/
│   │           ├── useRouteSelection.ts   # 选中方案的状态与副作用
│   │           └── useResultsInit.ts      # 结果页初始化（数据加载 + 初始动画）
│   │
│   ├── components/                    # 跨页面公共组件
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx          # 全局 Layout：Aura + Noise + Nav + Outlet
│   │   │   ├── Navbar.tsx             # 顶部导航（Logo + 面包屑 + 偏好按钮）
│   │   │   └── Breadcrumb.tsx         # 面包屑（仅 ResultsPage 可见）
│   │   │
│   │   ├── overlays/
│   │   │   ├── TransitionOverlay.tsx  # 幕布转场覆盖层（GSAP 驱动）
│   │   │   └── FilterDrawer.tsx       # 出行偏好侧边抽屉
│   │   │
│   │   ├── background/
│   │   │   ├── AuraBackground.tsx     # 光晕背景（鼠标跟随）
│   │   │   └── NoiseTexture.tsx       # 噪点纹理叠层
│   │   │
│   │   └── map/
│   │       ├── AmapContainer.tsx      # 高德地图宿主容器（处理加载和销毁）
│   │       └── PulseMapOverlay.tsx    # SVG 路线叠加层（绘制在高德地图之上）
│   │
│   ├── animations/                    # 所有 GSAP 动画，与 React 完全解耦
│   │   ├── curtain.ts                 # 幕布升起/落下转场
│   │   ├── reveal.ts                  # 元素入场（fadeUp、stagger）
│   │   ├── aura.ts                    # 光晕鼠标跟随
│   │   └── mapPath.ts                 # SVG 路线路径绘制动画
│   │
│   ├── stores/                        # Zustand 状态仓库
│   │   ├── searchStore.ts             # 搜索条件（出发/到达/日期）
│   │   ├── routeStore.ts              # 方案列表 + 选中的方案 index
│   │   └── uiStore.ts                 # 抽屉开关、主题模式（dawn/dusk）
│   │
│   ├── services/                      # 数据服务层
│   │   ├── api.ts                     # Axios 实例（baseURL、拦截器）
│   │   ├── routeService.ts            # searchRoutes()、fetchStopsByTrainNo()
│   │   └── mock/
│   │       └── routes.mock.ts         # 原型 mock 数据（接口未就绪时使用）
│   │
│   ├── types/                         # 全局 TypeScript 类型定义
│   │   ├── route.ts                   # Route、Segment、Seat、Stop 类型
│   │   ├── search.ts                  # SearchParams 类型
│   │   └── theme.ts                   # ThemeMode 类型
│   │
│   ├── styles/
│   │   ├── tokens.css                 # 设计令牌（CSS 变量，主题切换核心）
│   │   ├── fonts.css                  # 自托管字体 @font-face 声明
│   │   ├── scrollbar.css              # 全局滚动条样式（隐藏/自定义）
│   │   └── tailwind.css               # Tailwind 入口（@tailwind base/components/utilities）
│   │
│   ├── hooks/                         # 跨页面通用 hooks
│   │   ├── useTheme.ts                # 读写主题模式（绑定 uiStore + html attribute）
│   │   ├── useTimeGreeting.ts         # 根据时间返回问候语和主题模式
│   │   └── useMouseAura.ts            # 鼠标跟随光晕（封装 mousemove 监听）
│   │
│   └── utils/
│       ├── duration.ts                # 时间格式化（"4小时35分"）
│       ├── price.ts                   # 价格格式化（"¥860"）
│       └── seat.ts                    # 席别余票状态判断（充足/紧张/售罄）
│
├── .env.development                   # 本地环境变量（高德 Key、API BaseURL）
├── .env.production                    # 生产环境变量
├── tailwind.config.ts                 # Tailwind 扩展（VistaFlow 设计令牌注入）
├── vite.config.ts                     # Vite 配置
└── tsconfig.json                      # TypeScript 配置（严格模式）
```

---

## 4. 分层架构与职责边界

### 4.1 层级划分

```
┌─────────────────────────────────────────┐
│              Pages 页面层                │  ← 组合组件，处理页面级逻辑
├─────────────────────────────────────────┤
│           Components 组件层              │  ← 纯 UI，接受 Props，不知道 Store 存在
├───────────────────┬─────────────────────┤
│   Animations 动画  │   Hooks 逻辑钩子    │  ← 解耦动画/逻辑，供页面层调用
├───────────────────┴─────────────────────┤
│              Stores 状态层               │  ← 全局状态，页面层直接订阅
├─────────────────────────────────────────┤
│             Services 服务层              │  ← HTTP 请求、数据转换
├─────────────────────────────────────────┤
│               Types 类型层               │  ← 贯穿所有层的类型契约
└─────────────────────────────────────────┘
```

### 4.2 各层职责边界（铁律）

**Pages 层**
- ✅ 可以调用 Store（`useSearchStore`、`useRouteStore`、`useUiStore`）
- ✅ 可以调用 TanStack Query（`useQuery`、`useMutation`）
- ✅ 可以调用页面级 custom hook（`useHomeReveal`、`useRouteSelection`）
- ✅ 可以组合 Components 层的组件
- ❌ 不可以直接调用 `gsap.to()`
- ❌ 不可以直接调用 `axios`

**Components 层**
- ✅ 可以接受 Props 和 callback
- ✅ 可以有内部 local state（`useState`）
- ✅ 可以调用 `useTheme`、`useTimeGreeting` 等通用 hooks
- ❌ 不可以直接订阅 Store（由 Pages 层通过 Props 传入数据）
- ❌ 不可以调用 `gsap.to()`
- ❌ 不可以发起 HTTP 请求

**Animations 层**
- ✅ 只能接受 DOM ref 和参数，返回 GSAP Timeline 或 void
- ✅ 可以使用 GSAP 所有 API
- ❌ 不可以 import 任何 React 组件
- ❌ 不可以 import Store

**Services 层**
- ✅ 负责所有 Axios 调用
- ✅ 负责将原始 API 响应转换为 `types/` 中定义的类型
- ❌ 不可以包含 UI 逻辑
- ❌ 不可以直接操作 Store

---

## 5. 设计令牌系统

### 5.1 CSS 变量定义（`styles/tokens.css`）

所有颜色、动画时长均以 CSS 变量定义，主题切换通过切换 `html` 元素的 `data-theme` 属性实现：

```css
/* 日间模式（默认）—— dawn 主题 */
:root,
[data-theme="dawn"] {
  --color-bg:          #030303;
  --color-surface:     rgba(255, 255, 255, 0.03);
  --color-text-primary:   #F5F5F7;
  --color-text-muted:     #8A8A8E;
  --color-text-void:      #030303;

  /* 品牌强调色 */
  --color-pulse:       #E5C07B;       /* dawn 金色 */
  --color-pulse-rgb:   229, 192, 123; /* 用于 rgba() 计算 */

  /* 光晕背景色 */
  --aura-color-1:      #1a2a40;
  --aura-color-2:      rgba(229, 192, 123, 0.15);

  /* 地图路径色 */
  --map-path-color:    rgba(229, 192, 123, 0.3);

  /* 动画时长令牌 */
  --duration-fast:     0.3s;
  --duration-normal:   0.5s;
  --duration-slow:     0.8s;
  --duration-curtain:  0.8s;

  /* 缓动函数令牌 */
  --ease-out-expo:     cubic-bezier(0.19, 1, 0.22, 1);
  --ease-card:         cubic-bezier(0.19, 1, 0.22, 1);
}

/* 夜间模式 —— dusk 主题 */
[data-theme="dusk"] {
  --color-pulse:       #8B5CF6;       /* dusk 紫色 */
  --color-pulse-rgb:   139, 92, 246;

  --aura-color-1:      #110e24;
  --aura-color-2:      rgba(139, 92, 246, 0.15);
  --map-path-color:    rgba(139, 92, 246, 0.3);
}
```

### 5.2 Tailwind 令牌绑定（`tailwind.config.ts`）

```typescript
export default {
  theme: {
    extend: {
      colors: {
        void:      '#030303',
        starlight: '#F5F5F7',
        dawn:      '#E5C07B',
        dusk:      '#8B5CF6',
        muted:     '#8A8A8E',
        // 主题色绑定 CSS 变量，组件中使用 text-pulse、bg-pulse
        pulse:     'rgb(var(--color-pulse-rgb) / <alpha-value>)',
      },
      fontFamily: {
        sans:    ['Inter', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        serif:   ['"Cormorant Garamond"', 'serif'],
      },
      transitionDuration: {
        'fast':    'var(--duration-fast)',
        'normal':  'var(--duration-normal)',
        'slow':    'var(--duration-slow)',
      },
    },
  },
}
```

### 5.3 主题切换规范

主题切换**唯一入口**是 `useTheme` hook，禁止在组件中直接操作 `document.body.classList` 或 `html.setAttribute`：

```typescript
// hooks/useTheme.ts
export function useTheme() {
  const { mode, setMode } = useUiStore()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    localStorage.setItem('vf-theme', mode)
  }, [mode])

  return { mode, setMode }
}
```

---

## 6. 组件规范

### 6.1 组件分类与写法

**展示型组件（Presentational）**——绝大多数 `components/` 下的组件

```typescript
// 规范模板
interface RouteCardProps {
  route: Route           // 从 types/route.ts 导入
  isActive: boolean
  onSelect: (id: string) => void
  onStopsToggle: (trainNo: string) => void
}

export function RouteCard({ route, isActive, onSelect, onStopsToggle }: RouteCardProps) {
  // ✅ 只有 local UI state
  const [stopsExpanded, setStopsExpanded] = useState(false)

  // ✅ ref 用于动画
  const cardRef = useRef<HTMLDivElement>(null)

  return (
    <div ref={cardRef} className={cn('ticket-card', isActive && 'active')}>
      {/* ... */}
    </div>
  )
}
```

**容器型组件（Container）**——`pages/` 下的组件，负责连接 Store 和子组件

```typescript
// pages/ResultsPage/RouteList.tsx
export function RouteList() {
  // ✅ 容器层订阅 Store
  const routes = useRouteStore(s => s.routes)
  const selectedId = useRouteStore(s => s.selectedId)
  const selectRoute = useRouteStore(s => s.selectRoute)

  return (
    <div>
      {routes.map(route => (
        // ✅ 数据向下，事件向上
        <RouteCard
          key={route.id}
          route={route}
          isActive={route.id === selectedId}
          onSelect={selectRoute}
        />
      ))}
    </div>
  )
}
```

### 6.2 必须遵守的组件规则

- 所有组件使用**具名导出**（`export function Foo`），禁止默认导出（`export default`），保持 import 可追踪
- Props 命名使用完整单词，禁止缩写（`onSelect` 不写成 `onSel`）
- 每个组件文件**只导出一个主组件**，辅助子组件可以在同文件内定义但不对外导出
- 组件文件名与组件名**严格一致**（`RouteCard.tsx` → `export function RouteCard`）
- 使用 `cn()` 工具函数（`clsx` + `tailwind-merge`）合并 className，不使用字符串拼接

### 6.3 关键组件说明

**`TransitionOverlay`**
全局唯一，挂载在 `AppLayout` 中。接受来自 `uiStore` 的指令（`curtainUp` / `curtainDown`），内部通过 `animations/curtain.ts` 驱动 GSAP。页面跳转时序：

```
用户点击"生成方案"
  → uiStore.triggerCurtain('up')
  → TransitionOverlay 监听，执行 curtainUp 动画
  → 动画完成回调：router.navigate('/results')
  → ResultsPage 挂载，数据开始加载
  → uiStore.triggerCurtain('down')
  → TransitionOverlay 执行 curtainDown 动画
```

**`AmapContainer`**
高德地图的宿主。负责：加载高德 JS API（通过 `@amap/amap-jsapi-loader`）、初始化 Map 实例、在组件卸载时销毁实例（防内存泄漏）。将 `AMap.Map` 实例通过 ref 暴露给父组件，父组件不关心初始化细节。

**`PulseMapOverlay`**
纯 SVG 组件，**不依赖**高德 SDK。接受站点坐标数组（由高德地图实例将经纬度转换为像素坐标后传入），绘制路线路径动画。与高德地图的协作通过 `MapPanel` 协调，保持各自的独立性。

---

## 7. 状态管理契约

### 7.1 Store 设计原则

- 每个 Store 只负责**一个明确的业务域**，禁止跨域写入
- Store 中**只存可以被多个组件共享的状态**，组件内部状态用 `useState`
- Store 的 action 命名以动词开头：`setOrigin`、`selectRoute`、`toggleDrawer`

### 7.2 Store 定义

**`searchStore.ts`** —— 搜索条件域

```typescript
interface SearchState {
  origin: string        // 出发地，如 "北京"
  destination: string   // 目的地，如 "上海"
  date: string          // 日期，如 "3月25日"
  setOrigin: (v: string) => void
  setDestination: (v: string) => void
  setDate: (v: string) => void
  reset: () => void
}
```

**`routeStore.ts`** —— 方案数据域

```typescript
interface RouteState {
  routes: Route[]           // 方案列表
  selectedId: string | null // 当前选中的方案 ID
  sortMode: 'recommend' | 'duration' | 'price'
  setRoutes: (routes: Route[]) => void
  selectRoute: (id: string) => void
  deselectRoute: () => void
  setSortMode: (mode: SortMode) => void
}
```

**`uiStore.ts`** —— UI 交互域

```typescript
interface UIState {
  isDrawerOpen: boolean
  themeMode: 'dawn' | 'dusk'    // dawn = 日间金色，dusk = 夜间紫色
  curtainSignal: 'idle' | 'up' | 'down'  // 幕布动画信号
  toggleDrawer: () => void
  setThemeMode: (mode: ThemeMode) => void
  triggerCurtain: (direction: 'up' | 'down') => void
  resetCurtain: () => void
}
```

### 7.3 Store 订阅规则

组件订阅 Store 时，**只订阅自己需要的字段**，避免不必要的重渲染：

```typescript
// ✅ 正确：精确订阅
const selectedId = useRouteStore(s => s.selectedId)

// ❌ 错误：订阅整个 store，任何字段变化都会触发重渲染
const store = useRouteStore()
```

---

## 8. 动画系统契约

### 8.1 动画封装规范

`animations/` 目录下的每个函数必须满足：

- 接受 `HTMLElement | null` 类型的 ref 作为目标
- 返回 `gsap.core.Timeline` 或 `void`
- 不 import 任何 React API
- 不访问任何 Store

```typescript
// animations/curtain.ts 示例结构
import gsap from 'gsap'

export interface CurtainOptions {
  loadingTexts?: string[]
  onMidpoint?: () => void   // 幕布遮住屏幕时的回调（此时切换路由）
  onComplete?: () => void
}

export function curtainUp(
  overlayEl: HTMLElement,
  loadingBarEl: HTMLElement,
  loadingTextEl: HTMLElement,
  options: CurtainOptions = {}
): gsap.core.Timeline {
  // 返回 timeline，调用方可以 .pause() / .reverse()
  const tl = gsap.timeline()
  // ... GSAP 实现
  return tl
}

export function curtainDown(overlayEl: HTMLElement): gsap.core.Timeline {
  const tl = gsap.timeline()
  // ...
  return tl
}
```

### 8.2 在组件中使用动画

动画必须通过 custom hook 调用，**不得在组件内直接 import `animations/` 函数**：

```typescript
// pages/HomePage/hooks/useHomeReveal.ts
import { useEffect, useRef } from 'react'
import { revealUp } from '@/animations/reveal'

export function useHomeReveal() {
  const heroRef = useRef<HTMLDivElement>(null)
  const formRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!heroRef.current || !formRef.current) return
    revealUp([heroRef.current, formRef.current], { stagger: 0.2 })
  }, [])

  return { heroRef, formRef }
}
```

### 8.3 GSAP 注册

GSAP 插件只在 `main.tsx` 中注册一次：

```typescript
// main.tsx
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)
```

---

## 9. 地图集成规范

### 9.1 架构分层

高德地图的集成分三层，职责严格分离：

```
MapPanel（协调层）
  ├── AmapContainer（SDK 层）—— 管理高德实例生命周期
  └── PulseMapOverlay（可视化层）—— 纯 SVG，不依赖高德 SDK
```

### 9.2 高德地图样式配置

使用高德自定义地图样式平台（`loca.amap.com`）生成 `styleId`，通过环境变量注入：

```
# .env.development
VITE_AMAP_KEY=your_key_here
VITE_AMAP_STYLE_ID=amap://styles/your_style_id  # 自定义暗色样式
```

地图初始化参数：

```typescript
const map = new AMap.Map(containerRef.current, {
  mapStyle: import.meta.env.VITE_AMAP_STYLE_ID,
  zoom: 5,
  center: [116.4074, 39.9042],  // 默认中心：北京
  features: ['bg', 'road', 'building'],  // 关闭 POI 标注，保持简洁
  pitchEnable: false,
  rotateEnable: false,
})
```

### 9.3 坐标转换规范

高德地图使用 **GCJ-02 坐标系**（国测局坐标）。从后端获取的站点坐标如果是 WGS-84（GPS 标准），必须在 `services/` 层完成转换，不得在组件中处理坐标转换逻辑。

### 9.4 SVG 叠加层与高德的协作

`PulseMapOverlay` 不直接使用高德 API。协作流程：

1. `MapPanel` 拿到高德实例后，监听 `moveend` 和 `zoomend` 事件
2. 将路线上各站点的经纬度通过 `map.lngLatToContainer()` 转换为像素坐标
3. 将像素坐标数组以 Props 形式传给 `PulseMapOverlay`
4. `PulseMapOverlay` 根据像素坐标绘制 SVG 路径

这样 `PulseMapOverlay` 保持纯粹，可以独立测试和在非地图场景下复用。

---

## 10. 数据层规范

### 10.1 核心类型定义（`types/route.ts`）

```typescript
export type SeatStatus = '充足' | '紧张' | '余票有限' | '已售罄' | '无票'

export interface Seat {
  type: string        // "商务座" | "一等座" | "二等座" | "动卧" 等
  price: number       // 单位：元
  status: SeatStatus
}

export interface Stop {
  stationName: string
  arrivalTime: string   // "HH:mm" 格式
  dwellMinutes: number  // 停留分钟数
}

export interface TrainSegment {
  trainNo: string       // "G1"
  departure: string     // 出发站名
  arrival: string       // 到达站名
  departureTime: string // "HH:mm"
  arrivalTime: string   // "HH:mm"
  seats: Seat[]
  stops: Stop[]
  coordinates: {        // 站点坐标（GCJ-02）
    departure: [number, number]
    arrival: [number, number]
  }
}

export interface TransferNode {
  isTransfer: true
  description: string   // "济南西 同站换乘 • 预留 45 分钟"
  transferType: 'same-station' | 'cross-station'
  reserveMinutes: number
}

export type SegmentOrTransfer = TrainSegment | TransferNode

export interface Route {
  id: string
  label: string           // "最优直达" | "省时中转" 等
  departureTime: string   // 首段出发时间 "HH:mm"
  arrivalTime: string     // 末段到达时间 "HH:mm"
  totalMinutes: number    // 总耗时（分钟）
  basePrice: number       // 起步价（最低席别）
  isDirect: boolean
  segments: SegmentOrTransfer[]
}
```

### 10.2 服务层规范（`services/routeService.ts`）

```typescript
export interface SearchParams {
  origin: string
  destination: string
  date: string
}

// 对外暴露的函数签名
export async function searchRoutes(params: SearchParams): Promise<Route[]>
export async function fetchStopsByTrainNo(trainNo: string): Promise<Stop[]>
```

TanStack Query 的使用规范——在 Pages 层通过 custom hook 封装：

```typescript
// pages/ResultsPage/hooks/useResultsInit.ts
export function useResultsInit() {
  const { origin, destination, date } = useSearchStore()

  return useQuery({
    queryKey: ['routes', origin, destination, date],
    queryFn: () => searchRoutes({ origin, destination, date }),
    staleTime: 5 * 60 * 1000,  // 5 分钟内不重新请求
    enabled: !!(origin && destination && date),
  })
}
```

### 10.3 Mock 数据规范

开发阶段 mock 数据放在 `services/mock/routes.mock.ts`，结构必须严格符合 `Route[]` 类型。通过环境变量控制是否启用 mock：

```typescript
// services/routeService.ts
import { mockRoutes } from './mock/routes.mock'

export async function searchRoutes(params: SearchParams): Promise<Route[]> {
  if (import.meta.env.VITE_USE_MOCK === 'true') {
    await new Promise(r => setTimeout(r, 800))  // 模拟网络延迟
    return mockRoutes
  }
  const { data } = await api.get('/routes/search', { params })
  return data.map(transformRoute)  // 转换为内部类型
}
```

---

## 11. 路由规范

### 11.1 路由定义（`App.tsx`）

```typescript
export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="results" element={<ResultsPage />} />
        {/* 未来扩展：<Route path="booking/:routeId" element={<BookingPage />} /> */}
      </Route>
    </Routes>
  )
}
```

### 11.2 页面跳转规范

页面跳转**必须经过幕布动画**，不得直接调用 `navigate()`。跳转唯一入口：

```typescript
// hooks 层封装，pages 层调用
export function usePageTransition() {
  const navigate = useNavigate()
  const triggerCurtain = useUiStore(s => s.triggerCurtain)

  const transitionTo = useCallback((path: string) => {
    triggerCurtain('up')
    // TransitionOverlay 监听 curtainSignal，动画完成时调用 onMidpoint
    // onMidpoint 中执行 navigate(path)
  }, [navigate, triggerCurtain])

  return { transitionTo }
}
```

### 11.3 URL 设计

结果页将搜索参数写入 URL，支持分享和浏览器回退：

```
/results?from=北京&to=上海&date=2025-03-25
```

---

## 12. 工程规范与质量门禁

### 12.1 TypeScript 配置（`tsconfig.json`）

```json
{
  "compilerOptions": {
    "strict": true,           // 开启全部严格检查
    "noUncheckedIndexedAccess": true,  // 数组索引访问必须判空
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }     // 路径别名
  }
}
```

### 12.2 ESLint 规则（关键项）

```javascript
rules: {
  'no-restricted-imports': ['error', {
    patterns: [{
      // 禁止在 components/ 中直接导入 stores/
      group: ['*/stores/*'],
      importNames: ['useSearchStore', 'useRouteStore', 'useUiStore'],
      message: '组件层不可直接订阅 Store，请通过 Props 接收数据。'
    }, {
      // 禁止在 animations/ 中导入 React
      group: ['react', 'react-dom'],
      message: 'animations/ 层不可引用 React，保持与框架解耦。'
    }]
  }]
}
```

### 12.3 Git 提交规范

提交信息格式：`type(scope): description`

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | 缺陷修复 |
| `anim` | 动画调整（VistaFlow 专属类型）|
| `style` | 样式/令牌调整 |
| `refactor` | 重构（不改变行为）|
| `chore` | 构建/依赖 |

示例：
```
feat(results): add route sorting by price
anim(curtain): optimize midpoint timing for slower devices
fix(map): prevent memory leak on AmapContainer unmount
```

### 12.4 质量门禁（CI 必须全部通过）

```
pnpm typecheck    # TypeScript 类型检查，0 error
pnpm lint         # ESLint，0 error
pnpm test         # Vitest，coverage ≥ 80%（services/ 和 utils/ 强制）
pnpm build        # 生产构建，0 warning
```

---

## 13. 扩展性约定

本项目当前范围为 HomePage + ResultsPage，以下约定确保未来扩展不破坏现有结构：

### 13.1 新增页面

1. 在 `src/pages/` 下新建目录
2. 在 `App.tsx` 的 `<Routes>` 中添加路由
3. 在 `uiStore` 的 `curtainSignal` 或 `usePageTransition` hook 中无需改动（通用）
4. 如需新增 Store 域，新建独立 Store 文件，**不修改现有 Store**

### 13.2 新增主题

当前支持 `dawn`（金色）和 `dusk`（紫色）。新增主题步骤：

1. 在 `styles/tokens.css` 添加新的 `[data-theme="xxx"]` 块
2. 在 `types/theme.ts` 的 `ThemeMode` 联合类型中添加字面量
3. 在 `uiStore` 的 `themeMode` 联合类型中添加
4. 组件代码**无需改动**（全部通过 CSS 变量自动响应）

### 13.3 新增方案卡片字段

后端新增字段（如"碳排放量"）时：

1. 在 `types/route.ts` 的 `Route` 接口中添加可选字段
2. 在 `services/routeService.ts` 的 `transformRoute` 函数中处理映射
3. 在 `RouteCard.tsx` 中渲染（其他组件不受影响）

### 13.4 替换地图服务商

如未来需要从高德切换到其他地图（如腾讯地图），影响范围仅限：

- `components/map/AmapContainer.tsx` → 替换为新容器
- `pages/ResultsPage/MapPanel.tsx` → 调整坐标转换逻辑
- `PulseMapOverlay.tsx` **无需改动**（纯 SVG，与 SDK 解耦）

---

## 14. 禁止事项清单

以下行为在任何情况下不得出现，Code Review 发现直接打回：

**动画相关**
- ❌ 在 `.tsx` 文件中直接调用 `gsap.to()` / `gsap.from()` / `gsap.timeline()`
- ❌ 在 `animations/` 文件中 `import` React 或任何 Store
- ❌ 使用 CSS `transition` 实现幕布转场（必须用 GSAP 保持统一时序控制）

**状态相关**
- ❌ 在 `components/` 层直接调用 `useSearchStore` / `useRouteStore` / `useUiStore`
- ❌ 在 Store 的 action 中直接操作 DOM
- ❌ 多个 Store 之间互相直接 import

**样式相关**
- ❌ 在组件中 hardcode 颜色值（如 `color: '#E5C07B'`），必须使用 CSS 变量或 Tailwind 令牌
- ❌ 使用 `!important` 覆盖样式
- ❌ 在 `components/` 中使用内联 `style` 设置颜色（动画过渡中的 transform 除外）
- ❌ 直接操作 `document.body.classList` 切换主题（必须通过 `useTheme` hook）

**类型相关**
- ❌ 使用 `any` 类型（`@ts-ignore` 必须附注释说明原因）
- ❌ 在 `services/` 层将原始 API 响应直接传给组件（必须经过类型转换）
- ❌ 组件 Props 中出现 `object` 或非具名 interface

**地图相关**
- ❌ 在 `PulseMapOverlay` 中 import 高德 SDK
- ❌ 在组件中处理经纬度坐标系转换（必须在 `services/` 层完成）

---

*本文档由首席架构师起草，适用于 VistaFlow 前端项目全生命周期。文档变更须经架构评审，变更记录追加至本文档末尾。*