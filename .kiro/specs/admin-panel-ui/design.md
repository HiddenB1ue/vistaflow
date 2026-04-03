# Design Document: Admin Panel UI

## Overview

The VistaFlow Admin Panel is a single-page React application that replicates the HTML prototype at `apps/admin/prototype/vistaflow-admin.html` with pixel-perfect fidelity. It follows the same architectural patterns established in the web app (`apps/web`), adapted for an admin console context.

The admin panel uses a fixed sidebar + sticky header layout with 5 switchable views (no URL routing between views). It always uses the dusk (purple) theme. All UI interactions (drawers, modals, toasts, view switching) use GSAP or CSS transitions for animation, with animation logic isolated from components per the architecture contract.

The app uses mock data throughout — no real API integration is needed.

## Architecture

The admin panel follows the same layered architecture as the web app:

```
┌─────────────────────────────────────────┐
│              Pages 页面层                │  ← AdminLayout (sidebar + header + view container)
├─────────────────────────────────────────┤
│           Components 组件层              │  ← Pure UI, receives Props, no Store access
├───────────────────┬─────────────────────┤
│   Animations 动画  │   Hooks 逻辑钩子    │  ← Decoupled GSAP / logic, called by pages
├───────────────────┴─────────────────────┤
│              Stores 状态层               │  ← Zustand stores, subscribed by pages only
├─────────────────────────────────────────┤
│             Services 服务层              │  ← Mock data providers
├─────────────────────────────────────────┤
│               Types 类型层               │  ← TypeScript interfaces
└─────────────────────────────────────────┘
```

Key architectural decisions:

1. **View switching instead of routing**: The admin panel uses a Zustand `viewStore` to track the active view. No React Router page routes are needed (though React Router is installed for potential future use). Views are rendered conditionally and animated with GSAP.

2. **Always dusk theme**: Unlike the web app which switches between dawn/dusk, the admin panel hardcodes `data-theme="dusk"` on the HTML element. No theme switching logic is needed.

3. **Drawer/Modal pattern**: Drawers and modals are rendered at the root layout level (not inside views) and controlled via `uiStore`. This matches the prototype where drawers and the modal overlay sit outside the main content flow.

4. **Component reuse**: Shared UI primitives (GlassPanel, Badge, StatusDot, CustomSelect, ToggleSwitch, DataTable, ProgressBar, Toast) live in `components/ui/`. View-specific components live in `pages/{ViewName}/`.

```
src/
├── main.tsx
├── App.tsx
├── index.css
│
├── animations/
│   ├── viewTransition.ts      # View fade-in animation
│   └── panelReveal.ts         # Staggered glass panel reveal
│
├── components/
│   ├── background/
│   │   ├── AuraBackground.tsx
│   │   └── NoiseTexture.tsx
│   ├── layout/
│   │   ├── AdminLayout.tsx     # Root layout: sidebar + header + content + drawers + modal
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── overlays/
│   │   ├── DrawerBackdrop.tsx
│   │   ├── TaskDrawer.tsx
│   │   ├── StationDrawer.tsx
│   │   └── PreviewModal.tsx
│   └── ui/
│       ├── GlassPanel.tsx
│       ├── Badge.tsx
│       ├── StatusDot.tsx
│       ├── CustomSelect.tsx
│       ├── ToggleSwitch.tsx
│       ├── DataTable.tsx
│       ├── ProgressBar.tsx
│       ├── InputBox.tsx
│       ├── Button.tsx
│       ├── KpiCard.tsx
│       ├── SparklineChart.tsx
│       ├── DonutChart.tsx
│       ├── TaskCard.tsx
│       └── LogEntry.tsx
│
├── hooks/
│   ├── useViewTransition.ts    # Wraps animations/viewTransition.ts
│   └── usePanelReveal.ts       # Wraps animations/panelReveal.ts
│
├── pages/
│   ├── OverviewView.tsx
│   ├── TasksView.tsx
│   ├── DataView.tsx
│   ├── ConfigView.tsx
│   └── LogView.tsx
│
├── stores/
│   ├── viewStore.ts
│   ├── taskStore.ts
│   └── uiStore.ts
│
├── services/
│   └── mock/
│       ├── overview.mock.ts
│       ├── tasks.mock.ts
│       ├── stations.mock.ts
│       ├── logs.mock.ts
│       └── config.mock.ts
│
├── types/
│   ├── view.ts
│   ├── task.ts
│   ├── station.ts
│   ├── log.ts
│   └── config.ts
│
└── styles/
    ├── tokens.css
    └── fonts.css
```

## Components and Interfaces

### AdminLayout

The root layout component. Renders the sidebar, header, active view, drawers, modal, toast container, and background layers.

```typescript
// components/layout/AdminLayout.tsx
// No props — subscribes to viewStore, uiStore, taskStore at page level
// Renders:
//   <AuraBackground />
//   <NoiseTexture />
//   <ToastContainer />
//   <DrawerBackdrop />
//   <TaskDrawer />
//   <StationDrawer />
//   <PreviewModal />
//   <div className="flex h-screen overflow-hidden">
//     <Sidebar />
//     <main>
//       <Header />
//       <ViewContainer /> (conditionally renders active view)
//     </main>
//   </div>
```

### Sidebar

```typescript
interface SidebarProps {
  activeView: ViewId;
  pendingTaskCount: number;
  onNavigate: (viewId: ViewId) => void;
}
```

Renders the fixed left sidebar with logo, nav sections, nav items with icons, and user profile. The `pendingTaskCount` drives the yellow badge on the task scheduler nav item.

### Header

```typescript
interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh: () => void;
  timestamp: string;
}
```

Renders the sticky top bar with title, subtitle, refresh button, and timestamp.

### GlassPanel

```typescript
interface GlassPanelProps {
  children: React.ReactNode;
  className?: string;
}
```

A wrapper div applying the glass-morphism styles: `bg-white/[0.03] backdrop-blur-[20px] border border-white/[0.07] rounded-2xl hover:border-white/[0.13] transition-[border-color] duration-300`.

### Badge

```typescript
type BadgeVariant = 'green' | 'yellow' | 'blue' | 'red' | 'purple';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}
```

### StatusDot

```typescript
type StatusDotVariant = 'running' | 'pending' | 'idle' | 'error';

interface StatusDotProps {
  variant: StatusDotVariant;
}
```

### CustomSelect

```typescript
interface SelectOption {
  value: string;
  label: string;
}

interface CustomSelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}
```

Built on Radix UI `Select` primitive for accessibility, styled to match the prototype's custom dropdown appearance.

### ToggleSwitch

```typescript
interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}
```

Built on Radix UI `Switch` primitive.

### DataTable

```typescript
interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  getId: (row: T) => string;
}
```

### Button

```typescript
type ButtonVariant = 'primary' | 'outline' | 'danger' | 'warning' | 'success';
type ButtonSize = 'default' | 'sm';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}
```

### KpiCard

```typescript
interface KpiCardProps {
  label: string;
  value: string | number;
  accentColor?: string;       // left border color
  trend?: React.ReactNode;    // e.g., "+2,847 today"
  subtitle?: React.ReactNode;
  alertDot?: boolean;         // pinging dot next to label
}
```

### TaskCard

```typescript
interface TaskCardProps {
  task: Task;
  onStop?: (taskId: string) => void;
  onRestart?: (taskId: string) => void;
  onPreview?: (taskId: string) => void;
  onNavigateToConfig?: () => void;
  onShowDetails?: (taskId: string) => void;
}
```

### SparklineChart

```typescript
interface SparklineChartProps {
  data: number[];
  labels: string[];
  width?: number;
  height?: number;
}
```

Pure SVG component rendering a sparkline with gradient fill, line, data points, and x-axis labels.

### DonutChart

```typescript
interface DonutChartProps {
  percentage: number;
  label: string;
  sublabel?: string;
}
```

Pure SVG component rendering a donut/ring chart with centered text.

### LogEntry

```typescript
interface LogEntryProps {
  timestamp: string;
  severity: LogSeverity;
  message: React.ReactNode;
}
```

### Toast Container & Toast

```typescript
type ToastType = 'success' | 'error' | 'info' | 'warn';

interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}
```

### Drawers

```typescript
interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

interface StationDrawerProps {
  isOpen: boolean;
  station: Station | null;
  onClose: () => void;
  onSave: (station: Station) => void;
  onDelete: (stationId: string) => void;
}
```

### PreviewModal

```typescript
interface PreviewModalProps {
  isOpen: boolean;
  previewData: StationPreview[];
  onClose: () => void;
  onConfirm: (selectedIds: string[]) => void;
}
```

## Data Models

### View Types

```typescript
// types/view.ts
export type ViewId = 'view-overview' | 'view-tasks' | 'view-data' | 'view-config' | 'view-log';

export interface ViewConfig {
  id: ViewId;
  title: string;
  subtitle: string;
  navId: string;
}
```

### Task Types

```typescript
// types/task.ts
export type TaskStatus = 'running' | 'pending' | 'completed' | 'error' | 'terminated';

export type TaskType = 'fetch-status' | 'fetch-station' | 'geocode' | 'price' | 'cleanup';

export interface Task {
  id: string;
  name: string;
  type: TaskType;
  typeLabel: string;
  status: TaskStatus;
  description: string;
  cron?: string;
  metrics: {
    label: string;
    value: string;
  };
  timing: {
    label: string;
    value: string;
  };
  errorMessage?: string;
}
```

### Station Types

```typescript
// types/station.ts
export type CoordinateStatus = 'complete' | 'low-confidence' | 'missing';

export interface Station {
  id: string;
  name: string;
  code: string;
  city: string;
  longitude: number;
  latitude: number;
  coordinateStatus: CoordinateStatus;
  confidence?: number;
  dataSource: 'amap' | 'manual' | 'scraped';
  lastUpdated: string;
  notes?: string;
}

export interface StationPreview {
  id: string;
  name: string;
  code: string;
  longitude: number;
  latitude: number;
  confidence: number | null;
  failed: boolean;
}
```

### Log Types

```typescript
// types/log.ts
export type LogSeverity = 'SUCCESS' | 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';

export interface LogRecord {
  id: string;
  timestamp: string;
  severity: LogSeverity;
  message: string;
  highlightedTerms?: string[];
}
```

### Config Types

```typescript
// types/config.ts
export type CredentialHealth = 'healthy' | 'expired';

export interface ApiCredential {
  id: string;
  name: string;
  description: string;
  health: CredentialHealth;
  maskedKey: string;
  quotaInfo?: string;
  expiryWarning?: string;
}

export interface GlobalToggle {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}
```

### Store Interfaces

```typescript
// stores/viewStore.ts
interface ViewState {
  activeView: ViewId;
  switchView: (viewId: ViewId) => void;
}

// stores/taskStore.ts
interface TaskState {
  tasks: Task[];
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
}

// stores/uiStore.ts
interface UiState {
  taskDrawerOpen: boolean;
  stationDrawerOpen: boolean;
  stationDrawerData: Station | null;
  previewModalOpen: boolean;
  toasts: ToastItem[];
  openTaskDrawer: () => void;
  closeTaskDrawer: () => void;
  openStationDrawer: (station: Station) => void;
  closeStationDrawer: () => void;
  openPreviewModal: () => void;
  closePreviewModal: () => void;
  addToast: (message: string, type: ToastType) => void;
  removeToast: (id: string) => void;
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The following properties are derived from the acceptance criteria prework analysis. Each property is universally quantified and references the requirements it validates.

### Property 1: View switching updates store and header

*For any* valid ViewId, calling `switchView(viewId)` on the View_Store SHALL update `activeView` to that ViewId, and the Header component SHALL render the corresponding title and subtitle from the VIEW_CONFIG mapping.

**Validates: Requirements 2.3, 2.5, 14.1**

### Property 2: Active nav item matches active view

*For any* ViewId set as the active view, the Sidebar SHALL render exactly one navigation item with the active visual state (purple left border, purple-tinted background), and that item SHALL correspond to the active ViewId.

**Validates: Requirements 2.2**

### Property 3: Task card renders correct elements per status

*For any* Task object, the TaskCard component SHALL render a StatusDot variant, Badge variant, and action buttons that correspond to the task's `status` field: running → green dot + "Running" badge + "终止" button; pending → yellow dot + "Pending Confirm" badge + "预览并确认" button; completed → blue dot + "Completed" badge + "重新执行" button; error → red dot + "Error" badge + "去修复" button.

**Validates: Requirements 4.4, 4.5, 4.6, 4.7**

### Property 4: Task status transitions

*For any* task with status "running", calling `updateTaskStatus(taskId, 'terminated')` SHALL change the task's status to "terminated". *For any* task with status "completed", calling `updateTaskStatus(taskId, 'running')` SHALL change the task's status to "running". The task list length SHALL remain unchanged after any status update.

**Validates: Requirements 4.8, 4.9, 14.2**

### Property 5: Drawer submit triggers toast with task name

*For any* non-empty task name string entered in the TaskDrawer, clicking the submit button SHALL close the drawer (setting `taskDrawerOpen` to false) and add a toast to the UI_Store whose message contains the task name string.

**Validates: Requirements 5.4**

### Property 6: Backdrop/Escape closes any open drawer

*For any* drawer that is currently open (taskDrawerOpen or stationDrawerOpen is true), clicking the backdrop overlay or pressing the Escape key SHALL set that drawer's open state to false.

**Validates: Requirements 5.5, 5.6, 7.5**

### Property 7: Sub-tab switching shows correct panel

*For any* data management sub-tab (stations, routes, price), clicking that tab SHALL make its corresponding panel visible and hide all other sub-tab panels.

**Validates: Requirements 6.2**

### Property 8: Coordinate color matches station status

*For any* Station object rendered in the DataTable, the coordinate value cells SHALL use green text when `coordinateStatus` is "complete", yellow text when "low-confidence", and red text when "missing".

**Validates: Requirements 6.5**

### Property 9: Edit button opens drawer with correct station data

*For any* Station in the DataTable, clicking its edit button SHALL open the StationDrawer with `stationDrawerData` set to that Station object, and the drawer title SHALL contain the station's name.

**Validates: Requirements 6.7, 7.2**

### Property 10: Failed preview rows have red styling

*For any* StationPreview object where `failed` is true, the corresponding DataTable row in the PreviewModal SHALL render with a red-tinted background and red coordinate text.

**Validates: Requirements 8.5**

### Property 11: Modal footer reflects selection count

*For any* set of selected StationPreview items in the PreviewModal, the footer SHALL display the count of selected non-failed items and the count of skipped failed items, and these counts SHALL sum to the total number of preview items.

**Validates: Requirements 8.6**

### Property 12: Credential card renders per health status

*For any* ApiCredential object, the credential card SHALL render a green "正常可用" Badge when `health` is "healthy" and a red "已过期" Badge with red-tinted border when `health` is "expired".

**Validates: Requirements 9.3, 9.4**

### Property 13: Toggle switch flips state

*For any* ToggleSwitch component with initial checked state `s`, toggling it SHALL change its checked state to `!s`.

**Validates: Requirements 9.7**

### Property 14: Log entry severity badge color

*For any* LogRecord, the LogEntry component SHALL render a Badge whose color variant matches the severity: SUCCESS → green, INFO → blue, WARN → yellow, ERROR → red, SYSTEM → purple.

**Validates: Requirements 10.3**

### Property 15: Toast type determines styling

*For any* ToastType value, the rendered toast SHALL use the corresponding color scheme: success → green border/background/icon, error → red, info → purple, warn → yellow.

**Validates: Requirements 11.2**

### Property 16: Badge variant color mapping

*For any* BadgeVariant value (green, yellow, blue, red, purple), the Badge component SHALL render with the correct text color, border color, and background tint for that variant.

**Validates: Requirements 12.4**

### Property 17: Status dot variant rendering

*For any* StatusDotVariant value, the StatusDot component SHALL render with the correct color: running → green with blink animation, pending → yellow with glow, idle → blue, error → red with glow.

**Validates: Requirements 12.5**

### Property 18: Click outside closes custom select

*For any* CustomSelect component whose dropdown is currently open, a click event on an element outside the component SHALL close the dropdown.

**Validates: Requirements 12.8**

### Property 19: UI store drawer/modal/toast state management

*For any* sequence of open/close operations on the UI_Store, the drawer and modal open states SHALL accurately reflect the last operation performed. *For any* toast added via `addToast`, it SHALL appear in the `toasts` array, and calling `removeToast` with its id SHALL remove it.

**Validates: Requirements 14.3**

## Error Handling

Since this is a frontend UI with mock data and no real API integration, error handling is minimal:

1. **Missing mock data**: Components should gracefully handle empty arrays or null values by rendering empty states or placeholder content.
2. **Invalid view ID**: The `switchView` action should ignore invalid ViewId values and keep the current view active.
3. **Drawer/Modal state conflicts**: Only one drawer should be open at a time. Opening a new drawer should close any currently open drawer.
4. **Toast overflow**: The toast container should handle rapid toast additions without layout issues. Toasts auto-dismiss after 3.5 seconds.
5. **Custom Select edge cases**: Dropdowns should close on Escape key, outside click, and option selection. Multiple open selects should not be possible.

## Testing Strategy

### Dual Testing Approach

The admin panel uses both unit tests and property-based tests for comprehensive coverage:

- **Unit tests** (Vitest + React Testing Library): Verify specific rendering examples, edge cases, and integration points between components.
- **Property-based tests** (Vitest + fast-check): Verify universal properties across generated inputs.

### Property-Based Testing Configuration

- Library: `fast-check` (for TypeScript/Vitest integration)
- Minimum iterations: 100 per property test
- Each property test references its design document property with a tag comment:
  ```typescript
  // Feature: admin-panel-ui, Property 4: Task status transitions
  ```

### Test Organization

- Store tests: `stores/__tests__/viewStore.test.ts`, `taskStore.test.ts`, `uiStore.test.ts`
- Component tests: `components/ui/__tests__/Badge.test.tsx`, `StatusDot.test.tsx`, etc.
- View tests: `pages/__tests__/OverviewView.test.tsx`, etc.

### Key Testing Focus Areas

- **Stores** (Property tests): View switching, task status transitions, UI state management (Properties 1, 4, 5, 6, 13, 19)
- **UI Components** (Property tests): Badge/StatusDot/Toast variant rendering, CustomSelect outside-click behavior (Properties 14, 15, 16, 17, 18)
- **Task Cards** (Property tests): Status-to-visual mapping (Property 3)
- **Data Views** (Property tests): Coordinate color mapping, sub-tab switching (Properties 7, 8)
- **Unit tests**: Specific rendering checks for each view, drawer form interactions, modal selection logic
