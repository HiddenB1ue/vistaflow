# Implementation Plan: Admin Panel UI

## Overview

Build the VistaFlow admin panel as a pixel-perfect React implementation of the HTML prototype. Tasks are ordered to establish infrastructure first, then shared components, then views, then overlays, with testing integrated alongside implementation.

## Tasks

- [x] 1. Project infrastructure and configuration
  - [x] 1.1 Install dependencies (Tailwind CSS 4, @tailwindcss/vite, Zustand 4, GSAP 3.12, @radix-ui/react-select, @radix-ui/react-switch, @radix-ui/react-dialog, react-router-dom) and update `apps/admin/package.json`
    - _Requirements: 1.1_
  - [x] 1.2 Configure Vite with `@tailwindcss/vite` plugin and `@` path alias in `vite.config.ts`
    - _Requirements: 1.2_
  - [x] 1.3 Update `tsconfig.app.json` with strict mode, `noUncheckedIndexedAccess`, and `@/*` path alias
    - _Requirements: 1.5_
  - [x] 1.4 Create `src/styles/tokens.css` with dusk-theme CSS variables and `src/styles/fonts.css` with Google Fonts imports
    - _Requirements: 1.3_
  - [x] 1.5 Rewrite `src/index.css` with Tailwind CSS 4 `@theme` directive, custom colors, font families, and global styles (scrollbar, body, glass-panel, status-dot animations, input-box, btn variants, data-table, drawer, modal, toggle, custom-select, toast, badge, nav-item, log-line, progress-bar, tab-btn, sparkline styles) matching the prototype CSS
    - _Requirements: 1.4, 12.1, 12.3, 12.4, 12.5, 12.6, 12.7_

- [x] 2. Type definitions and mock data
  - [x] 2.1 Create type files: `types/view.ts`, `types/task.ts`, `types/station.ts`, `types/log.ts`, `types/config.ts` with all interfaces from the design document
    - _Requirements: 14.1, 14.2, 14.3_
  - [x] 2.2 Create mock data files: `services/mock/overview.mock.ts`, `tasks.mock.ts`, `stations.mock.ts`, `logs.mock.ts`, `config.mock.ts` with data matching the prototype content
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [x] 3. Zustand stores
  - [x] 3.1 Implement `stores/viewStore.ts` managing activeView with switchView action
    - _Requirements: 14.1_
  - [x] 3.2 Implement `stores/taskStore.ts` managing task list with updateTaskStatus action, initialized from mock data
    - _Requirements: 14.2_
  - [x] 3.3 Implement `stores/uiStore.ts` managing drawer/modal open states, stationDrawerData, and toast queue with add/remove actions
    - _Requirements: 14.3_
  - [ ]* 3.4 Write property tests for viewStore (Property 1: view switching updates activeView)
    - **Property 1: View switching updates store and header**
    - **Validates: Requirements 2.3, 2.5, 14.1**
  - [ ]* 3.5 Write property tests for taskStore (Property 4: task status transitions preserve list length and update status)
    - **Property 4: Task status transitions**
    - **Validates: Requirements 4.8, 4.9, 14.2**
  - [ ]* 3.6 Write property tests for uiStore (Property 19: drawer/modal/toast state management)
    - **Property 19: UI store drawer/modal/toast state management**
    - **Validates: Requirements 14.3**

- [x] 4. Checkpoint - Ensure all store tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Animation system and hooks
  - [x] 5.1 Create `animations/viewTransition.ts` with GSAP fade-in function for view switching
    - _Requirements: 13.1, 13.3_
  - [x] 5.2 Create `animations/panelReveal.ts` with GSAP staggered fade-up function for glass panels
    - _Requirements: 13.1, 13.4_
  - [x] 5.3 Create `hooks/useViewTransition.ts` wrapping viewTransition animation
    - _Requirements: 13.2_
  - [x] 5.4 Create `hooks/usePanelReveal.ts` wrapping panelReveal animation
    - _Requirements: 13.2_

- [x] 6. Shared UI components
  - [x] 6.1 Implement `components/ui/GlassPanel.tsx`, `components/ui/Button.tsx`, `components/ui/InputBox.tsx`
    - _Requirements: 12.1_
  - [x] 6.2 Implement `components/ui/Badge.tsx` with five color variants
    - _Requirements: 12.4_
  - [x] 6.3 Implement `components/ui/StatusDot.tsx` with four status variants
    - _Requirements: 12.5_
  - [x] 6.4 Implement `components/ui/CustomSelect.tsx` using Radix UI Select primitive with prototype styling and outside-click close behavior
    - _Requirements: 12.2, 12.8_
  - [x] 6.5 Implement `components/ui/ToggleSwitch.tsx` using Radix UI Switch primitive
    - _Requirements: 12.3_
  - [x] 6.6 Implement `components/ui/DataTable.tsx` with selectable rows, column rendering, and hover states
    - _Requirements: 12.6_
  - [x] 6.7 Implement `components/ui/ProgressBar.tsx`
    - _Requirements: 12.7_
  - [x] 6.8 Implement `components/ui/KpiCard.tsx`, `components/ui/SparklineChart.tsx`, `components/ui/DonutChart.tsx`
    - _Requirements: 3.1, 3.3, 3.4_
  - [x] 6.9 Implement `components/ui/TaskCard.tsx` rendering status-specific elements per task status
    - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7_
  - [x] 6.10 Implement `components/ui/LogEntry.tsx` with severity-colored badge
    - _Requirements: 10.3_
  - [ ]* 6.11 Write property tests for Badge variant color mapping (Property 16)
    - **Property 16: Badge variant color mapping**
    - **Validates: Requirements 12.4**
  - [ ]* 6.12 Write property tests for StatusDot variant rendering (Property 17)
    - **Property 17: Status dot variant rendering**
    - **Validates: Requirements 12.5**
  - [ ]* 6.13 Write property tests for TaskCard status-to-visual mapping (Property 3)
    - **Property 3: Task card renders correct elements per status**
    - **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
  - [ ]* 6.14 Write property tests for LogEntry severity badge color (Property 14)
    - **Property 14: Log entry severity badge color**
    - **Validates: Requirements 10.3**

- [x] 7. Checkpoint - Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Background and layout components
  - [x] 8.1 Implement `components/background/AuraBackground.tsx` and `components/background/NoiseTexture.tsx` (adapted from web app, using dusk aura colors)
    - _Requirements: 1.3_
  - [x] 8.2 Implement `components/layout/Sidebar.tsx` with logo, nav sections, nav items with icons, active state highlighting, notification badges, and user profile
    - _Requirements: 2.1, 2.2, 2.6_
  - [x] 8.3 Implement `components/layout/Header.tsx` with title, subtitle, refresh button, and timestamp
    - _Requirements: 2.4, 2.5_
  - [x] 8.4 Implement `components/layout/AdminLayout.tsx` composing sidebar, header, view container, drawers, modal, toast container, and background layers
    - _Requirements: 2.1, 2.3_

- [x] 9. Toast system
  - [x] 9.1 Implement `components/ui/ToastContainer.tsx` rendering toasts from uiStore with GSAP enter/exit animations and auto-dismiss after 3.5s
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  - [ ]* 9.2 Write property tests for toast type styling (Property 15)
    - **Property 15: Toast type determines styling**
    - **Validates: Requirements 11.2**

- [x] 10. View implementations
  - [x] 10.1 Implement `pages/OverviewView.tsx` with KPI cards grid, sparkline chart, donut chart, active tasks list, and system alerts panel
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  - [x] 10.2 Implement `pages/TasksView.tsx` with KPI cards, search/filter bar, and task card list with stop/restart/preview actions
    - _Requirements: 4.1, 4.2, 4.3, 4.8, 4.9, 4.10_
  - [x] 10.3 Implement `pages/DataView.tsx` with sub-tabs, station data table with coordinate color coding, pagination, and placeholder panels for routes/pricing
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  - [x] 10.4 Implement `pages/ConfigView.tsx` with credential cards (healthy/expired), connection test button with loading state, and global toggle switches
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  - [x] 10.5 Implement `pages/LogView.tsx` with search/filter bar and log entry list
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 11. Overlay components (drawers and modal)
  - [x] 11.1 Implement `components/overlays/DrawerBackdrop.tsx` with click-to-close behavior
    - _Requirements: 5.5, 7.5_
  - [x] 11.2 Implement `components/overlays/TaskDrawer.tsx` with form fields (name, type select, date offset, cron toggle, retry config), submit and cancel actions
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_
  - [x] 11.3 Implement `components/overlays/StationDrawer.tsx` with station edit form fields, save/delete/cancel actions
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 11.4 Implement `components/overlays/PreviewModal.tsx` with filter bar, data table with checkboxes, failed row styling, selection count footer, and confirm action
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 12. Wire App.tsx and main.tsx
  - [x] 12.1 Update `src/App.tsx` to render AdminLayout as the root component with dusk theme initialization
    - _Requirements: 1.3, 2.1_
  - [x] 12.2 Update `src/main.tsx` to import index.css and register GSAP plugins
    - _Requirements: 13.1_
  - [x] 12.3 Update `apps/admin/index.html` with correct title, font preloads, and root div
    - _Requirements: 1.3_

- [x] 13. Final checkpoint - Ensure all tests pass and app renders correctly
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses TypeScript with React 19, Tailwind CSS 4, Zustand 4, GSAP 3.12, and Radix UI primitives
