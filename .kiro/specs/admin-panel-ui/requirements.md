# Requirements Document

## Introduction

VistaFlow Admin Panel（运营控制台）是 VistaFlow 高铁出行规划平台的后台管理界面。该面板为运营人员提供数据监控、任务调度、数据管理、系统配置和操作日志五大核心功能。UI 必须与 HTML 原型 `apps/admin/prototype/vistaflow-admin.html` 像素级一致，并复用 Web 端已验证的架构模式（React 19 + TypeScript + Tailwind CSS 4 + Zustand + GSAP）。Admin 面板始终使用 dusk（紫色）主题。

## Glossary

- **Admin_Panel**: VistaFlow 运营控制台 React 应用，运行于 `apps/admin`
- **Sidebar**: 左侧固定导航栏，包含 Logo、导航菜单项和用户信息
- **Header**: 顶部粘性标题栏，显示当前视图标题、副标题、刷新按钮和时间戳
- **View**: SPA 内的视图区域，通过侧边栏导航切换，共 5 个视图
- **Glass_Panel**: 毛玻璃效果面板组件，使用 `backdrop-filter: blur` 和半透明背景
- **Custom_Select**: 自定义下拉选择器组件，替代原生 `<select>`，带动画展开/收起
- **Toggle_Switch**: 自定义拨动开关组件，带激活态动画
- **Toast_System**: 全局通知提示系统，支持 success/error/info/warn 四种类型
- **Drawer**: 侧边抽屉面板，从右侧滑入，带遮罩层
- **Modal**: 居中弹窗组件，带遮罩层和缩放动画
- **Status_Dot**: 状态指示灯组件，不同状态对应不同颜色和动画
- **Badge**: 标签徽章组件，支持 green/yellow/blue/red/purple 五种颜色
- **KPI_Card**: 关键指标卡片，显示数值、趋势和辅助信息
- **Sparkline_Chart**: 迷你折线图 SVG 组件，用于数据趋势展示
- **Donut_Chart**: 环形图 SVG 组件，用于配额使用率展示
- **Data_Table**: 数据表格组件，带表头、行悬停、复选框和分页
- **Task_Card**: 任务卡片组件，显示任务状态、信息和操作按钮
- **Log_Entry**: 日志条目组件，显示时间戳、级别徽章和日志内容
- **View_Store**: Zustand 状态仓库，管理当前活跃视图和视图切换
- **Task_Store**: Zustand 状态仓库，管理任务列表和任务状态
- **UI_Store**: Zustand 状态仓库，管理抽屉/弹窗开关、Toast 队列等 UI 状态
- **Design_Token**: CSS 变量定义的设计令牌，控制颜色、字体、间距等视觉属性
- **Mock_Data**: 模拟数据，用于在无后端 API 时填充界面

## Requirements

### Requirement 1: 项目基础设施配置

**User Story:** As a developer, I want the admin app to have all required dependencies and build configuration, so that I can develop and build the admin panel with the same toolchain as the web app.

#### Acceptance Criteria

1. THE Admin_Panel SHALL include dependencies for Tailwind CSS 4, Zustand 4, GSAP 3.12, Radix UI Primitives, and React Router in `package.json`
2. THE Admin_Panel SHALL configure Vite with `@tailwindcss/vite` plugin and `@` path alias resolving to `src/`
3. THE Admin_Panel SHALL define Design_Token CSS variables in `styles/tokens.css` matching the dusk theme values from the prototype
4. THE Admin_Panel SHALL configure Tailwind CSS 4 `@theme` directive with custom colors (void, starlight, dawn, dusk, muted, pulse) and font families (sans: Inter, display: Space Grotesk, serif: Cormorant Garamond)
5. THE Admin_Panel SHALL set TypeScript strict mode with `noUncheckedIndexedAccess` and path alias `@/*` mapping to `src/*`

### Requirement 2: 全局布局与导航

**User Story:** As an admin user, I want a persistent sidebar and header layout, so that I can navigate between views and see contextual information at all times.

#### Acceptance Criteria

1. THE Sidebar SHALL render as a fixed 240px-wide left column with the VistaFlow logo, "Admin Console" subtitle, navigation sections ("数据运营" and "系统"), and a user profile area at the bottom
2. THE Sidebar SHALL highlight the active navigation item with a left purple border and purple-tinted background
3. WHEN a navigation item is clicked, THE Admin_Panel SHALL switch to the corresponding View with a GSAP fade-in animation
4. THE Header SHALL render as a sticky top bar displaying the current View title, subtitle, a refresh button, and a timestamp
5. WHEN the active View changes, THE Header SHALL update its title and subtitle to match the selected View configuration
6. THE Sidebar navigation items SHALL display notification badges where applicable (e.g., pending task count on "任务调度中心")

### Requirement 3: 概览仪表板视图 (Overview Dashboard)

**User Story:** As an admin user, I want to see a dashboard with key metrics and system status, so that I can quickly assess the health and activity of the platform.

#### Acceptance Criteria

1. THE View SHALL display four KPI_Card components in a responsive grid: total database records, station count with coordinate completion rate, pending alerts count, and daily API call count
2. THE KPI_Card components SHALL display accent-colored left borders (green for stations, yellow for alerts, purple for API calls) matching the prototype
3. THE View SHALL display a Sparkline_Chart showing data entry trends for the last 7 days with a purple gradient fill and labeled x-axis dates
4. THE View SHALL display a Donut_Chart showing API quota usage percentage with a purple stroke and centered percentage text
5. THE View SHALL display an active tasks summary list with Status_Dot indicators and Badge components for each task state
6. THE View SHALL display a system alerts panel with color-coded alert cards (warning in yellow, info in purple, success in green)
7. WHEN the View is activated, THE Glass_Panel components SHALL animate in with a staggered GSAP fade-up effect

### Requirement 4: 任务调度中心视图 (Task Scheduler)

**User Story:** As an admin user, I want to manage data processing tasks, so that I can monitor, create, and control automated data operations.

#### Acceptance Criteria

1. THE View SHALL display four KPI_Card components: active/total tasks, running count, pending confirmation count, and error count
2. THE View SHALL display a search input and a Custom_Select status filter for filtering tasks
3. THE View SHALL display Task_Card components for each task, each showing a Status_Dot, Badge, task type label, title, description, and relevant metrics
4. THE Task_Card for a running task SHALL display a green blinking Status_Dot, a "Running" Badge, fetched record count, and elapsed time in monospace green text
5. THE Task_Card for a pending-confirm task SHALL display a yellow Status_Dot, a "Pending Confirm" Badge, a yellow-highlighted border, and a "预览并确认" warning button
6. THE Task_Card for a completed task SHALL display a blue Status_Dot, a "Completed" Badge, reduced opacity, and a "重新执行" button
7. THE Task_Card for an error task SHALL display a red Status_Dot, an "Error" Badge, a red-highlighted border, error description, and a "去修复" button
8. WHEN the "终止" button on a running task is clicked, THE Task_Card SHALL update its Status_Dot to red, Badge to "Terminated", and display a Toast notification
9. WHEN the "重新执行" button on a completed task is clicked, THE Task_Card SHALL update its Status_Dot to green blinking, Badge to "Running", and display a Toast notification
10. WHEN the "新建任务" button is clicked, THE Admin_Panel SHALL open the task creation Drawer

### Requirement 5: 任务创建抽屉 (Task Creation Drawer)

**User Story:** As an admin user, I want to create new data processing tasks through a side panel form, so that I can configure and deploy new automated operations.

#### Acceptance Criteria

1. THE Drawer SHALL slide in from the right edge with a cubic-bezier ease animation and activate a backdrop overlay
2. THE Drawer SHALL contain form fields: task name input, task type Custom_Select (with 5 options), target date offset input, cron toggle with cron expression input, and retry configuration inputs
3. WHEN the cron Toggle_Switch is toggled off, THE Drawer SHALL visually dim the cron expression section
4. WHEN the "部署任务" button is clicked, THE Drawer SHALL close, and THE Toast_System SHALL display a success message with the task name
5. WHEN the backdrop overlay is clicked, THE Drawer SHALL close
6. WHEN the Escape key is pressed, THE Drawer SHALL close

### Requirement 6: 数据管理视图 (Data Management)

**User Story:** As an admin user, I want to browse and edit station data, so that I can maintain the accuracy of the platform's geographic database.

#### Acceptance Criteria

1. THE View SHALL display sub-tab buttons for "车站数据", "线路数据", and "票价矩阵"
2. WHEN a sub-tab is clicked, THE View SHALL show the corresponding data panel and hide others
3. THE stations sub-tab SHALL display a search input, a status Custom_Select filter, a "导出 CSV" button, and a "新增站点" button
4. THE stations sub-tab SHALL display a Data_Table with columns: checkbox, station name, code, city, longitude, latitude, coordinate status Badge, last updated timestamp, and an action button
5. THE Data_Table rows SHALL display coordinate values in green monospace for complete stations, yellow for low-confidence stations, and red for missing-coordinate stations
6. THE Data_Table SHALL include a pagination footer showing total count, current range, and previous/next page buttons
7. WHEN the "编辑" button on a station row is clicked, THE Admin_Panel SHALL open the station edit Drawer with that station's data
8. THE "线路数据" and "票价矩阵" sub-tabs SHALL display placeholder panels with icons and descriptive text

### Requirement 7: 站点编辑抽屉 (Station Edit Drawer)

**User Story:** As an admin user, I want to edit station details in a side panel, so that I can correct or update geographic data without leaving the data management view.

#### Acceptance Criteria

1. THE Drawer SHALL display form fields: station name, station code, city, longitude (green monospace), latitude (green monospace), coordinate confidence progress bar, data source Custom_Select, and a notes textarea
2. THE Drawer title SHALL update to show the station name being edited
3. WHEN the "保存" button is clicked, THE Drawer SHALL close and THE Toast_System SHALL display a success message
4. WHEN the "删除" button is clicked, THE Drawer SHALL close and THE Toast_System SHALL display an error-styled deletion message
5. WHEN the backdrop overlay is clicked or Escape is pressed, THE Drawer SHALL close

### Requirement 8: 数据预览确认弹窗 (Data Preview Modal)

**User Story:** As an admin user, I want to review geocoding results before committing them to the database, so that I can verify data quality and exclude failed entries.

#### Acceptance Criteria

1. THE Modal SHALL display centered with a backdrop overlay, scale-in animation, and a maximum width of approximately 80% viewport
2. THE Modal SHALL contain a header with a yellow "Manual Action Required" label, title text, and a close button
3. THE Modal SHALL contain a filter bar with a search input and a status Custom_Select (解析成功项/解析失败项/全部)
4. THE Modal SHALL display a Data_Table with columns: checkbox, station name, station code, pre-parsed longitude, pre-parsed latitude, and confidence Badge
5. THE Data_Table rows for failed entries SHALL display red-tinted background, red coordinate values, and a red "Failed" Badge
6. THE Modal footer SHALL display a count of selected items and skipped failures, a "取消" button, and a "确认并落库" primary button
7. WHEN the "确认并落库" button is clicked, THE Modal SHALL close and THE Toast_System SHALL display a success message

### Requirement 9: 系统配置视图 (System Config)

**User Story:** As an admin user, I want to manage API credentials and global behavior switches, so that I can maintain external service integrations and control system behavior.

#### Acceptance Criteria

1. THE View SHALL display a description paragraph explaining the configuration purpose
2. THE View SHALL display API credential cards in a two-column grid: one for the map service API (healthy state with green Badge) and one for the proxy credential (expired state with red Badge and red-tinted border)
3. THE healthy credential card SHALL display masked API key text, quota information, "修改配置" and "连通性检测" buttons
4. THE expired credential card SHALL display token text with expiry warning in red, "更新凭证" and "清除覆盖值" danger buttons
5. WHEN the "连通性检测" button is clicked, THE button SHALL show a spinning loader for approximately 1.6 seconds, then THE Toast_System SHALL display a success message with latency info
6. THE View SHALL display a "全局行为开关" Glass_Panel with four Toggle_Switch items: auto-retry (on), preview before write (on), email alerts (off), and maintenance mode (off)
7. WHEN a Toggle_Switch is toggled, THE Toggle_Switch SHALL visually update its active state

### Requirement 10: 操作日志视图 (Operation Logs)

**User Story:** As an admin user, I want to view system operation logs, so that I can audit activities and troubleshoot issues.

#### Acceptance Criteria

1. THE View SHALL display a search input, a severity Custom_Select filter (所有级别/INFO/WARN/ERROR/SUCCESS), and an "导出日志" button
2. THE View SHALL display Log_Entry components inside a Glass_Panel with monospace font styling
3. EACH Log_Entry SHALL display a timestamp, a severity Badge (color-coded: green for SUCCESS, blue for INFO, yellow for WARN, red for ERROR, purple for SYSTEM), and a log message with highlighted identifiers
4. THE Log_Entry list SHALL render all mock log entries matching the prototype content and ordering

### Requirement 11: Toast 通知系统

**User Story:** As an admin user, I want to see feedback notifications for my actions, so that I can confirm operations succeeded or understand what went wrong.

#### Acceptance Criteria

1. THE Toast_System SHALL render toast notifications in a fixed container at the bottom-right of the viewport
2. THE Toast_System SHALL support four toast types: success (green), error (red), info (purple), and warn (yellow), each with a matching icon, border color, and background tint
3. WHEN a toast is triggered, THE Toast_System SHALL animate the toast in with a GSAP slide-up fade-in effect
4. THE Toast_System SHALL automatically dismiss each toast after approximately 3.5 seconds with a GSAP slide-down fade-out animation
5. THE Toast_System SHALL support displaying multiple toasts simultaneously, stacked vertically with a gap

### Requirement 12: 共享 UI 组件库

**User Story:** As a developer, I want reusable UI components matching the prototype's design language, so that I can build all views consistently and efficiently.

#### Acceptance Criteria

1. THE Glass_Panel component SHALL render a container with semi-transparent background (`rgba(255,255,255,0.03)`), `backdrop-filter: blur(20px)`, a subtle border (`rgba(255,255,255,0.07)`), 16px border-radius, and a hover state that brightens the border
2. THE Custom_Select component SHALL render a trigger button with a chevron icon, and WHEN clicked, SHALL display an animated dropdown with selectable options that update the trigger label
3. THE Toggle_Switch component SHALL render a 44x24px track with a 20px circular thumb, transitioning between inactive (white/10 background) and active (purple background with dark thumb) states
4. THE Badge component SHALL support five color variants (green, yellow, blue, red, purple) with matching text color, border, and background tint, using Space Grotesk font with uppercase tracking
5. THE Status_Dot component SHALL render an 8px circle with color and animation variants: running (green with blink animation and glow), pending (yellow with glow), idle (blue), and error (red with glow)
6. THE Data_Table component SHALL render with Space Grotesk uppercase headers, consistent cell padding, bottom borders, and row hover highlighting
7. THE Progress_Bar component SHALL render a 4px-height track with a colored fill bar and smooth width transition
8. WHEN a Custom_Select dropdown is open and the user clicks outside of the dropdown, THE Custom_Select SHALL close the dropdown

### Requirement 13: 动画系统

**User Story:** As a developer, I want GSAP animations isolated from component logic, so that animations remain maintainable and consistent with the web app's architecture.

#### Acceptance Criteria

1. THE Admin_Panel SHALL isolate all GSAP animation functions in the `animations/` directory, with no direct `gsap.to()` calls in component files
2. THE Admin_Panel SHALL expose animation functions to components exclusively through custom hooks in the `hooks/` directory
3. WHEN a View is switched, THE Admin_Panel SHALL apply a GSAP opacity fade-in animation to the incoming View content
4. WHEN Glass_Panel components first appear in a View, THE Admin_Panel SHALL apply a staggered GSAP fade-up animation
5. THE Drawer open/close animations SHALL use CSS transitions with `cubic-bezier(0.19, 1, 0.22, 1)` easing matching the prototype

### Requirement 14: 状态管理

**User Story:** As a developer, I want well-structured Zustand stores, so that application state is predictable and components receive data through props.

#### Acceptance Criteria

1. THE View_Store SHALL manage the active view identifier and provide an action to switch views
2. THE Task_Store SHALL manage the task list with typed task objects and provide actions to update individual task states (running, pending, completed, error, terminated)
3. THE UI_Store SHALL manage drawer open/close state, modal open/close state, and toast notification queue
4. THE Admin_Panel components in the `components/` directory SHALL NOT directly subscribe to any Zustand store; data SHALL flow through props from page-level components
5. EACH Zustand store SHALL be defined in a separate file under `stores/` with a named export

### Requirement 15: Mock 数据

**User Story:** As a developer, I want realistic mock data, so that all views render with content matching the prototype without requiring a backend API.

#### Acceptance Criteria

1. THE Admin_Panel SHALL provide mock data for overview KPI values, sparkline chart data points, and API quota percentages matching the prototype
2. THE Admin_Panel SHALL provide mock data for four task objects (running, pending-confirm, completed, error) with all fields matching the prototype content
3. THE Admin_Panel SHALL provide mock data for five station records (上海虹桥站, 北京南站, 上饶站, 新余北站, 测试站点 A) with all fields matching the prototype
4. THE Admin_Panel SHALL provide mock data for twelve log entries with timestamps, severity levels, and messages matching the prototype content
5. THE Admin_Panel SHALL provide mock data for two API credential configurations (healthy map API, expired proxy token) matching the prototype
6. THE Admin_Panel SHALL provide mock data for four global toggle switch configurations matching the prototype default states
