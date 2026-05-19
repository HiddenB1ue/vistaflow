## ADDED Requirements

### Requirement: Price store for global price state
The frontend SHALL maintain a dedicated `priceStore` that holds a global `priceMap` (keyed by `trainNo:fromStation:toStation`), streaming status (`isStreaming`), and progress counters (`totalLegs`, `fetchedLegs`).

#### Scenario: Store initialization on search
- **WHEN** a new search completes and the user lands on the results page
- **THEN** the priceStore is reset and `isStreaming` is set to `false`
- **AND** `priceMap` is empty

#### Scenario: Merging price batch
- **WHEN** a `leg_priced` event is received from the price stream
- **THEN** the priceStore merges the new price entries into `priceMap`
- **AND** `fetchedLegs` counter is incremented

### Requirement: Route store price integration
The `routeStore` SHALL expose an `updateRoutesPrices` action that applies price data from `priceStore.priceMap` to the current routes list, updating each segment's `seats` and `ticketStatus`.

#### Scenario: Updating route with available price
- **WHEN** `updateRoutesPrices` is called
- **AND** a segment's `price_map_key` exists in `priceMap` with `failed: false`
- **THEN** the segment's `seats` array is populated from the price entry
- **AND** the segment's `ticketStatus` is set to `"ready"`
- **AND** the parent route's `ticketStatus` is recomputed based on all segments

#### Scenario: Updating route with failed price
- **WHEN** `updateRoutesPrices` is called
- **AND** a segment's `price_map_key` exists in `priceMap` with `failed: true`
- **THEN** the segment's `ticketStatus` is set to `"unavailable"`
- **AND** the segment's `seats` array remains empty

#### Scenario: Route with no price data yet
- **WHEN** `updateRoutesPrices` is called
- **AND** a segment's `price_map_key` does NOT exist in `priceMap`
- **THEN** the segment's `ticketStatus` remains `"loading"`

### Requirement: Price stream lifecycle in JourneyPage
The `JourneyPage` component SHALL start a price stream connection when it mounts with a valid `searchId`, and abort the connection on unmount or when `searchId` changes.

#### Scenario: Auto-start price stream on mount
- **WHEN** the JourneyPage mounts with a valid searchId
- **THEN** a SSE connection is opened to `POST /{searchId}/prices/stream`
- **AND** incoming price events update priceStore and routeStore

#### Scenario: Cleanup on unmount
- **WHEN** the JourneyPage unmounts (e.g., user navigates back to search)
- **THEN** the active price stream SSE connection is aborted
- **AND** priceStore is reset

#### Scenario: New search replaces old stream
- **WHEN** searchId changes (user performs a new search)
- **THEN** the previous price stream is aborted
- **AND** priceStore is reset before starting the new stream

### Requirement: Loading skeleton for price display
Route cards and segment cards SHALL display an animated skeleton placeholder when `ticketStatus` is `"loading"`.

#### Scenario: RouteCard price area in loading state
- **WHEN** a route has `ticketStatus: "loading"`
- **THEN** the price area displays a pulsing skeleton placeholder instead of a price value

#### Scenario: RouteSegmentCard seats in loading state
- **WHEN** a segment has `ticketStatus: "loading"`
- **THEN** the seats grid displays skeleton placeholders (4 animated blocks)

#### Scenario: Transition from loading to ready
- **WHEN** a segment's price data arrives and `ticketStatus` changes from `"loading"` to `"ready"`
- **THEN** the skeleton is replaced with actual seat/price data without a full page re-render

### Requirement: Price loading progress indicator
The results page SHALL display a compact progress indicator showing the status of ongoing price fetching.

#### Scenario: Progress shown during streaming
- **WHEN** `priceStore.isStreaming` is `true`
- **THEN** a progress indicator is visible showing fetched/total legs (e.g., "票价查询中 3/15")

#### Scenario: Progress hidden after completion
- **WHEN** the price stream completes (`pricing_complete` event received)
- **THEN** the progress indicator is hidden

### Requirement: Price sort disabled during streaming
The "按价格排序" sort option SHALL be disabled while price streaming is active.

#### Scenario: Price sort button disabled
- **WHEN** `priceStore.isStreaming` is `true`
- **THEN** the price sort option is visually disabled with a tooltip explaining prices are still loading

#### Scenario: Price sort enabled after completion
- **WHEN** `priceStore.isStreaming` becomes `false` (stream completed)
- **THEN** the price sort option becomes clickable and functional

### Requirement: Search progress overlay removes pricing phase
The `SearchProgressOverlay` SHALL no longer display pricing-related progress (since pricing happens on the results page).

#### Scenario: Overlay shows only planning phases
- **WHEN** a search is in progress
- **THEN** the overlay shows planning and building_view phases only
- **AND** does NOT show "正在查询票价" or pricing progress bar
