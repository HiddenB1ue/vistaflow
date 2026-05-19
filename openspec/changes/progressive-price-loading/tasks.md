## 1. Schema & Type Changes

- [x] 1.1 Add `"loading"` to `TicketStatus` and `SegmentTicketStatus` in `apps/api/app/journey_search_sessions/schemas.py`
- [x] 1.2 Add `"loading"` to `Route.ticketStatus` and `TrainSegment.ticketStatus` in `apps/web/src/types/route.ts`

## 2. Backend — Modify create_session to skip pricing

- [x] 2.1 In `JourneySearchSessionService.create_session`, remove the `_prefetch_session_prices` call and price_map usage; pass `ticketStatus="loading"` to built routes
- [x] 2.2 Add a `_mark_route_loading` helper method (similar to `_mark_route_disabled`) that sets all segments and route ticketStatus to `"loading"`
- [x] 2.3 Update `_build_view_result` to use `_mark_route_loading` when no price_map is provided and tickets are requested
- [x] 2.4 Update `get_view` to handle `"loading"` status — read from Redis, return `"loading"` for uncached segments instead of blocking

## 3. Backend — Per-leg callback in Ticket12306Service

- [x] 3.1 Add `OnLegCompleteCallback` type alias and `on_leg_complete` parameter to `prefetch_all_prices`
- [x] 3.2 After each leg fetch completes (success or failure), build price entries for all segments in that leg and invoke `on_leg_complete`
- [x] 3.3 Invoke `on_leg_complete` for cached legs (those already in Redis) with their existing data
- [x] 3.4 Add unit tests for the per-leg callback behavior

## 4. Backend — New price stream endpoint

- [x] 4.1 Add `stream_prices` method to `JourneySearchSessionService` that loads context/candidates and calls `prefetch_all_prices` with a progress callback
- [x] 4.2 Add `POST /{search_id}/prices/stream` SSE endpoint in `router.py` with event types: `pricing_started`, `leg_priced`, `pricing_complete`, `error`
- [x] 4.3 Handle invalid/expired search_id gracefully (emit error event and close)
- [x] 4.4 Add integration test for the price stream endpoint

## 5. Frontend — Price store

- [x] 5.1 Create `apps/web/src/stores/priceStore.ts` with `priceMap`, `isStreaming`, `totalLegs`, `fetchedLegs`, `mergePrices`, `startStream`, `endStream`, `reset` actions

## 6. Frontend — Price stream service

- [x] 6.1 Create `apps/web/src/services/priceStreamService.ts` with `startPriceStream(searchId, onPriceBatch, onComplete, onError)` returning an abort function
- [x] 6.2 Implement SSE parsing: handle `pricing_started`, `leg_priced`, `pricing_complete`, `error` events

## 7. Frontend — Route store integration

- [x] 7.1 Add `updateRoutesPrices(priceMap)` action to `routeStore.ts` that merges price data into current routes' segments
- [x] 7.2 Implement ticketStatus computation: segment ready/unavailable/loading based on priceMap; route-level status derived from all segments

## 8. Frontend — JourneyPage price stream lifecycle

- [x] 8.1 Add useEffect in `JourneyPage/index.tsx` to start price stream when searchId is available, abort on cleanup
- [x] 8.2 Wire up priceStore and routeStore: on each `leg_priced` batch, call `mergePrices` then `updateRoutesPrices`

## 9. Frontend — UI loading states

- [x] 9.1 Update `RouteCard.tsx` price area to show skeleton when `route.ticketStatus === 'loading'`
- [x] 9.2 Update `RouteSegmentCard.tsx` seats grid to show skeleton placeholders when `segment.ticketStatus === 'loading'`
- [x] 9.3 Add compact price loading progress indicator to `RouteListPanel.tsx` (e.g., "票价查询中 3/15")
- [x] 9.4 Disable price sort option in sort controls when `priceStore.isStreaming === true`

## 10. Frontend — SearchProgressOverlay cleanup

- [x] 10.1 Remove pricing phase display (`pricing_started`, `leg_fetched`, progress bar) from `SearchProgressOverlay.tsx`
- [x] 10.2 Remove `pricing` phase from `searchProgressStore.ts` phases (keep idle, planning, building_view, complete, error)

## 11. Verification

- [x] 11.1 Run backend tests: `cd apps/api && uv run pytest --cov=app`
- [x] 11.2 Run backend lint/type check: `cd apps/api && uv run ruff check . && uv run mypy app`
- [x] 11.3 Run frontend build: `pnpm build:web`
- [x] 11.4 Run frontend tests: `pnpm test:web`
- [ ] 11.5 Manual smoke test: search flow → immediate results → progressive price fill-in
