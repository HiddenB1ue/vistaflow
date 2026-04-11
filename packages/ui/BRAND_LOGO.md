# VistaFlow Brand Logo 使用指南

## 概述

为了确保 VistaFlow 品牌标识在所有页面和应用中保持一致的样式和位置，我们统一使用 `TopbarBrand` 组件。

## 推荐方案：使用 TopbarBrand 组件

`TopbarBrand` 是一个公共组件，适用于所有需要显示 VistaFlow Logo 的场景。

### 为什么统一使用 TopbarBrand？

1. **样式一致性**：自动应用统一的 Logo 样式（字体、大小、字间距等）
2. **灵活性**：支持可选的点击事件，未来扩展方便
3. **语义清晰**：明确表示这是品牌标识
4. **维护简单**：只需维护一个组件

### 基本用法

```tsx
import { TopbarBrand } from '@vistaflow/ui';

// 静态显示（无点击）
<TopbarBrand>VistaFlow</TopbarBrand>

// 可点击（如返回首页）
<TopbarBrand onClick={() => navigateTo('/')}>VistaFlow</TopbarBrand>

// 自定义颜色
<TopbarBrand style={{ color: 'var(--color-starlight)' }}>VistaFlow</TopbarBrand>
```

## 布局规范

### 导航栏 / 顶栏 (Topbar)

在 `Topbar` 容器中使用（自动处理 padding）：

```tsx
import { Topbar, TopbarBrand } from '@vistaflow/ui';

<Topbar>
  <TopbarBrand onClick={handleClick}>VistaFlow</TopbarBrand>
</Topbar>
```

**Padding 规范：**
- 水平：`var(--vf-page-gutter-x)` = `clamp(1.5rem, 3vw, 3rem)` (24px-48px)
- 垂直：`var(--vf-page-gutter-y)` = `clamp(1.25rem, 2vw, 2rem)` (20px-32px)

### 侧边栏 (Sidebar)

Logo 区域应使用相同的 padding 变量：

```tsx
import { TopbarBrand } from '@vistaflow/ui';

<div className="vf-page-gutter" style={{ paddingBlock: 'var(--vf-page-gutter-y)' }}>
  <TopbarBrand>VistaFlow</TopbarBrand>
</div>
```

### 登录页 / 独立页面

在卡片或容器中使用：

```tsx
import { TopbarBrand } from '@vistaflow/ui';

<TopbarBrand style={{ color: 'var(--color-starlight)' }}>
  VistaFlow
</TopbarBrand>
```

## 当前应用示例

### 1. 用户端 (Web App)
**位置：** `apps/web/src/components/layout/Navbar.tsx`
```tsx
import { TopbarBrand } from '@vistaflow/ui';

<TopbarBrand onClick={() => navigateTo('/')}>VistaFlow</TopbarBrand>
```

### 2. 管理端侧边栏 (Admin Sidebar)
**位置：** `apps/admin/src/components/layout/Sidebar.tsx`
```tsx
import { TopbarBrand } from '@vistaflow/ui';

<div className="vf-page-gutter" style={{ paddingBlock: 'var(--vf-page-gutter-y)' }}>
  <TopbarBrand>{SIDEBAR_LABELS.brand}</TopbarBrand>
</div>
```

### 3. 管理端登录页 (Admin Login)
**位置：** `apps/admin/src/pages/LoginView.tsx`
```tsx
import { TopbarBrand } from '@vistaflow/ui';

<TopbarBrand style={{ color: 'var(--color-starlight)' }}>
  VistaFlow
</TopbarBrand>
```

## CSS 类（备用方案）

如果在特殊情况下无法使用 `TopbarBrand` 组件，可以使用 `.vf-brand-logo` CSS 类：

```tsx
<div className="vf-brand-logo">VistaFlow</div>
```

**注意：** 优先使用 `TopbarBrand` 组件，CSS 类仅作为备用方案。

## 样式规范

无论使用组件还是 CSS 类，Logo 样式都保持一致：

- 字体：`Space Grotesk` (font-display)
- 大小：`1.125rem` (18px)
- 粗细：`500` (medium)
- 字间距：`0.22em`
- 大小写：`uppercase`
- 颜色：`#fff` (白色，可覆盖)

## 重要提示

1. **优先使用 TopbarBrand 组件**：确保样式和行为的一致性

2. **使用 CSS 变量控制 padding**：
   - 水平：`var(--vf-page-gutter-x)` 或 `.vf-page-gutter` 类
   - 垂直：`var(--vf-page-gutter-y)`

3. **响应式设计**：CSS 变量会根据视口大小自动调整，无需手动处理

4. **颜色覆盖**：如果需要不同的颜色，使用内联样式覆盖：
   ```tsx
   <TopbarBrand style={{ color: 'var(--color-starlight)' }}>
     VistaFlow
   </TopbarBrand>
   ```

5. **点击事件**：即使当前不需要点击，也使用 `TopbarBrand`，方便未来扩展

## 新页面开发清单

在创建新页面时，确保：

- [ ] 使用 `TopbarBrand` 组件显示品牌标识
- [ ] 使用 `var(--vf-page-gutter-x)` 和 `var(--vf-page-gutter-y)` 控制 padding
- [ ] 测试不同视口大小下的显示效果
- [ ] 与现有页面对比，确保位置一致

## 相关文件

- 组件定义：`packages/ui/src/components/Topbar.tsx`
- CSS 定义：`packages/ui/src/styles/partials/layout-surfaces.css`
- CSS 变量：`packages/design-tokens/src/base.css`
