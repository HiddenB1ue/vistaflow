# VistaFlow 字体与排版系统

## 概述

VistaFlow 采用完全统一的字体与排版系统，所有字体家族、字号、字重、间距等都通过 `packages/design-tokens` 统一管理。

## 统一管理

所有排版相关配置都在 `packages/design-tokens` 中：

```
packages/design-tokens/
├── src/
│   ├── fonts.css          # 字体导入（Google Fonts）
│   ├── theme.css          # CSS 变量定义（字体家族、字号、间距）
│   ├── typography.css     # 排版工具类
│   ├── reset.css          # 基础字体应用
│   └── index.css          # 统一入口
```

**使用方式：**
```css
@import '@vistaflow/design-tokens';
```

## CSS 变量

在 `packages/design-tokens/src/theme.css` 中定义：

### 字体家族
```css
--font-body: "Inter", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
--font-display: "Space Grotesk", "Noto Sans SC", sans-serif;
--font-serif: "Crimson Pro", "Noto Serif SC", serif;
```

### 字号
```css
--text-xs: 0.65rem;      /* 10.4px */
--text-sm: 0.68rem;      /* 10.88px */
--text-base: 0.76rem;    /* 12.16px */
--text-md: 0.95rem;      /* 15.2px */
--text-lg: 1.2rem;       /* 19.2px */
--text-xl: 1.5rem;       /* 24px */
```

### 字间距
```css
--tracking-tight: 0.05em;
--tracking-normal: 0.1em;
--tracking-wide: 0.12em;
--tracking-wider: 0.18em;
--tracking-widest: 0.2em;
--tracking-ultra: 0.24em;
```

## 字体家族

### 1. 正文字体（Body Text）
```css
font-family: 'Inter', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

**用途：**
- 正文内容
- 表单输入
- 数据展示
- 描述性文本

**特点：**
- Inter：现代、清晰、专业的无衬线字体
- Noto Sans SC（思源黑体）：Google 开源，与 Inter 完美搭配
- 优秀的屏幕显示效果
- 支持多种字重（300-700）

### 2. 标题字体（Headings / Serif）
```css
font-family: 'Crimson Pro', 'Noto Serif SC', serif;
```

**用途：**
- 页面大标题
- 问候语（"早安"、"晚安"）
- 诗意文案
- 强调性标题

**特点：**
- Crimson Pro：优雅的衬线字体，支持斜体
- Noto Serif SC（思源宋体）：Google 开源宋体
- 优雅、有文化感
- 适合情感化表达

**CSS 类：**
- `.font-serif` - 应用衬线字体
- 通常配合 `italic` 使用

### 3. 标签/按钮字体（Display / Labels）
```css
font-family: 'Space Grotesk', 'Noto Sans SC', sans-serif;
```

**用途：**
- 按钮文字
- 导航标签
- 小标题（eyebrow）
- 数据标签
- 徽章（badge）

**特点：**
- Space Grotesk：几何感强，科技感十足
- 紧凑、清晰
- 适合大写字母（uppercase）

**CSS 类：**
- `.font-display` - 应用展示字体
- 通常配合 `uppercase` 和 `letter-spacing` 使用

## CSS 变量

在 `packages/design-tokens/src/theme.css` 中定义：

```css
--font-display: "Space Grotesk", "Noto Sans SC", sans-serif;
--font-serif: "Crimson Pro", "Noto Serif SC", serif;
```

## 字体加载

### 统一管理方式

字体通过 `packages/design-tokens/src/fonts.css` 统一加载：

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,300;0,400;1,300;1,400&family=Space+Grotesk:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@300;400;500;600;700&display=swap');
```

**优点：**
- 所有应用自动获得字体
- 只需维护一个地方
- 避免重复加载
- 便于版本管理

### 在应用中使用

只需在应用的入口 CSS 文件中导入：

```css
/* apps/web/src/index.css 或 apps/admin/src/index.css */
@import '@vistaflow/design-tokens';
```

**不需要**在 HTML 文件中添加 `<link>` 标签。

### 字重说明

- **300** - Light（轻）
- **400** - Regular（常规）
- **500** - Medium（中等）
- **600** - SemiBold（半粗）
- **700** - Bold（粗体）

## 使用示例

### 正文
```tsx
<p className="text-base">
  这是正文内容，使用 Inter + Noto Sans SC
</p>
```

### 标题
```tsx
<h1 className="font-serif italic text-4xl">
  优雅的标题，使用 Crimson Pro + Noto Serif SC
</h1>
```

### 按钮/标签
```tsx
<button className="font-display uppercase tracking-widest">
  按钮文字，使用 Space Grotesk + Noto Sans SC
</button>
```

## 设计原则

1. **统一性**：中英文字体风格协调统一
2. **可读性**：优先考虑屏幕显示效果
3. **层次感**：通过字体家族区分内容层级
4. **情感化**：衬线字体用于营造优雅氛围
5. **现代感**：无衬线字体保持科技感

## 注意事项

1. 标题使用 `font-serif` 时，建议配合 `italic` 使用
2. 标签使用 `font-display` 时，建议配合 `uppercase` 和 `letter-spacing` 使用
3. 中文字体会自动回退到 Noto Sans SC 或 Noto Serif SC
4. 所有字体均为开源字体，可免费商用

## 字体来源

- **Inter**: [https://rsms.me/inter/](https://rsms.me/inter/)
- **Crimson Pro**: [https://fonts.google.com/specimen/Crimson+Pro](https://fonts.google.com/specimen/Crimson+Pro)
- **Space Grotesk**: [https://fonts.google.com/specimen/Space+Grotesk](https://fonts.google.com/specimen/Space+Grotesk)
- **Noto Sans SC**: [https://fonts.google.com/noto/specimen/Noto+Sans+SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC)
- **Noto Serif SC**: [https://fonts.google.com/noto/specimen/Noto+Serif+SC](https://fonts.google.com/noto/specimen/Noto+Serif+SC)
