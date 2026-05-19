## Why

用户搜索车程方案后，必须等待所有票价从 12306 查询完毕才能看到结果列表。票价查询是最慢的环节（几十个 leg 逐个请求），导致用户在过渡页等待 10-30 秒。实际上用户更关心"有哪些车可坐"，票价信息可以延迟展示。

## What Changes

- 搜索流程不再阻塞于票价查询：`create_session` 跳过 pricing 阶段，方案规划完成后立即返回结果
- 新增渐进式票价加载 SSE 端点：前端在结果页挂载后开启独立的票价流，逐 leg 推送票价数据
- 路线/坐席展示支持 `loading` 状态：票价未到达前显示骨架屏，到达后实时更新
- 前端新增票价状态管理：独立的 priceStore 管理全局票价映射，与 routeStore 联动更新显示

## Capabilities

### New Capabilities
- `price-streaming`: 独立的票价 SSE 推流能力，接收 searchId 后逐 leg 查询并推送票价结果
- `progressive-ui-update`: 前端渐进式票价填充，包括 loading 态骨架屏、实时合并更新、进度指示

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- **Backend API**: 新增 `POST /journey-search-sessions/{search_id}/prices/stream` SSE 端点；修改 `create_session` 不再同步预取票价
- **Backend Service**: `Ticket12306Service.prefetch_all_prices` 增加 per-leg 完成回调；`JourneySearchSessionService` 新增 `stream_prices` 方法
- **Schema**: `TicketStatus` / `SegmentTicketStatus` 增加 `"loading"` 枚举值
- **Frontend Types**: `Route.ticketStatus` 和 `TrainSegment.ticketStatus` 增加 `"loading"` 值
- **Frontend Services**: 新建 `priceStreamService.ts`
- **Frontend Stores**: 新建 `priceStore.ts`；修改 `routeStore.ts` 增加票价合并 action
- **Frontend Components**: `RouteCard`、`RouteSegmentCard`、`SearchProgressOverlay`、`JourneyPage` 适配 loading 态
- **排序兼容**: 按价格排序在票价未全部到达时需禁用或标注不完整
