## Context

当前搜索流程为 planning → pricing → building_view 串行执行，用户需等待所有票价查询完毕（10-30s）才能看到结果。票价查询本质上是逐 leg 调用 12306 接口，受并发限制（semaphore=2）且易超时。

现有关键组件：
- `Ticket12306Service.prefetch_all_prices`: 批量查询所有 leg 票价，支持 `on_progress` 回调
- `JourneySearchSessionService.create_session`: 串行执行三阶段
- 前端 SSE `/stream` 端点: 流式推送 planning/pricing/building_view 进度
- Redis 缓存: 按 `ticket:leg:{date}:{from_code}:{to_code}` 存储 leg 级别票价数据
- `price_map_key`: `trainNo:fromStation:toStation` 作为 segment 到价格的映射 key

## Goals / Non-Goals

**Goals:**
- 用户搜索后 1-3 秒内看到完整的车次方案列表（无票价）
- 票价以渐进方式逐 leg 填充到结果页，每查到一批就更新对应的 RouteCard
- 保持翻页、筛选、排序等现有功能正常工作
- 保持对 Redis 票价缓存的复用，已缓存的 leg 直接推送

**Non-Goals:**
- 不改变 12306 票价查询的底层实现（cookie/proxy/并发策略）
- 不做 WebSocket 替代，继续使用 SSE
- 不引入独立的后台任务队列（直接在 SSE 连接中执行查询）
- 暂不做"只查当前页"的优化（全量查询，翻页时利用缓存）

## Decisions

### D1: 票价推送采用独立 SSE 端点

**选择**: 新增 `POST /{search_id}/prices/stream` 独立 SSE 端点

**替代方案**:
- A) 在现有 `/stream` 中继续推送票价 → 需要先发完整 `complete` 结果再继续发 pricing 事件，打破了现有"一个 SSE 流对应一次完整创建"的语义
- B) 客户端轮询 `get_view` → 每次翻页/刷新都重新查 Redis 能行，但无法做到实时逐条填充

**理由**: 独立端点职责单一，前端挂载后自行建连，生命周期与结果页绑定；旧版 `create_session` 逻辑不受影响。

### D2: 全量 candidates 查询，而非仅当前页

**选择**: price stream 加载 search context 中所有 candidates 的票价

**理由**: 12306 按 leg（日期+出发站+到达站）粒度查询，一个 leg 可能覆盖多条 route 的多个 segment。全量查询后写入 Redis，后续翻页、排序直接命中缓存，无需再次网络请求。

**Trade-off**: 首页票价出现会比"仅查当前页"稍慢（多几秒），但避免了翻页时的延迟抖动。

### D3: ticketStatus 新增 "loading" 枚举值

**选择**: 在 TicketStatus 和 SegmentTicketStatus 中新增 `"loading"` 状态

**替代方案**: 复用 `"disabled"` 表示未加载 → 语义不清，前端无法区分"不查询"和"正在查询中"

### D4: 前端用独立 priceStore + routeStore 联动

**选择**: 新建 `priceStore` 存全局 priceMap，收到批次后更新 routeStore 中当前页 routes

**替代方案**: 直接在 routeStore 里处理所有票价逻辑 → priceMap 是跨页全局的，放 routeStore 会使单个 store 过于臃肿

### D5: 按价格排序在 streaming 中的行为

**选择**: 当 `priceStore.isStreaming === true` 时，前端禁用"按价格排序"按钮并显示 tooltip

**理由**: 不完整的价格数据排序会误导用户。全量加载完后自动启用。

### D6: per-leg 回调粒度

**选择**: 每个 leg 查询完后立即推送该 leg 对应的所有 segment 的 `PriceCacheEntry`

**理由**: leg 是 12306 查询的原子单位，每个 leg 完成即可推送，延迟最小。一次 SSE event 可能包含多个 price_map_key（同 leg 下多趟车）。

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Price stream 中断（网络断开、后端异常） | 前端静默处理，已收到的票价保留；用户翻页时 `get_view` 的 `enrich_routes_for_view` 从 Redis 补读 |
| 并发多次搜索导致多个 price stream | 前端 useEffect cleanup 中 abort 旧 stream；priceStore.reset() 清理旧数据 |
| 大量 candidates（500+）导致 stream 时间过长 | 沿用现有 max_concurrency=2 限制，前端有进度指示；未来可考虑按页优先级 |
| 前端 React re-render 频繁（每 leg 触发一次 state update） | 使用 batch 更新：一个 leg 包含多个 key 合并后一次 setState；zustand 的 shallow compare 限制不必要的 re-render |
| `get_view` 在 stream 进行中被调用（翻页） | get_view 从 Redis 读已缓存价格，stream 已写入的部分都能读到；未缓存的返回 loading |
