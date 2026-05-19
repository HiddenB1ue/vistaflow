## ADDED Requirements

### Requirement: Session creation skips pricing phase
`create_session` SHALL complete after planning and building_view phases without performing ticket price pre-fetching. All routes in the response SHALL have `ticketStatus` set to `"loading"`. The SSE `/stream` endpoint SHALL no longer emit `pricing_started` or `leg_fetched` events.

#### Scenario: Fast session creation without pricing
- **WHEN** a client calls `POST /journey-search-sessions/stream` with valid search parameters
- **THEN** the SSE stream emits `phase:planning`, `plan_ready`, `candidates_counted`, `phase:building_view`, and `complete` events
- **AND** the `complete` event payload contains routes with `ticketStatus: "loading"` for all route items and segments
- **AND** no `pricing_started` or `leg_fetched` events are emitted

#### Scenario: Non-streaming session creation
- **WHEN** a client calls `POST /journey-search-sessions` (non-SSE endpoint)
- **THEN** the response contains routes with `ticketStatus: "loading"` for all items and segments
- **AND** the response is returned without waiting for ticket price queries

### Requirement: Independent price streaming endpoint
The system SHALL provide a `POST /journey-search-sessions/{search_id}/prices/stream` SSE endpoint that accepts a valid `search_id` and streams ticket price results as they are fetched from 12306.

#### Scenario: Successful price stream startup
- **WHEN** a client opens a connection to `POST /{search_id}/prices/stream` with a valid search_id
- **THEN** the system emits a `pricing_started` event containing `totalLegs`, `cachedLegs`, and `legsToFetch` counts
- **AND** immediately pushes any cached leg prices as `leg_priced` events

#### Scenario: Progressive leg price delivery
- **WHEN** the system finishes querying one leg from 12306
- **THEN** the system emits a `leg_priced` event containing a `prices` dictionary keyed by `price_map_key` (`trainNo:fromStation:toStation`) with corresponding `PriceCacheEntry` data (min_price, seats, matched_by, failed)
- **AND** the same data is written to Redis cache for subsequent reads

#### Scenario: Price stream completion
- **WHEN** all legs have been queried (or failed)
- **THEN** the system emits a `pricing_complete` event
- **AND** closes the SSE connection

#### Scenario: Invalid or expired search_id
- **WHEN** a client opens a connection with an invalid or expired search_id
- **THEN** the system emits an `error` event with an appropriate message
- **AND** closes the SSE connection

### Requirement: Price stream per-leg callback
`Ticket12306Service.prefetch_all_prices` SHALL accept an optional `on_leg_complete` callback that is invoked after each leg query completes, providing the price entries for all segments covered by that leg.

#### Scenario: Callback invoked per leg
- **WHEN** `prefetch_all_prices` is called with `on_leg_complete` callback
- **AND** a leg query to 12306 completes successfully
- **THEN** the callback is invoked with a dictionary of `price_map_key → PriceCacheEntry` for all segments in that leg

#### Scenario: Callback invoked for cached legs
- **WHEN** `prefetch_all_prices` finds a leg already cached in Redis
- **THEN** the `on_leg_complete` callback is invoked with the cached data for that leg's segments

#### Scenario: Callback invoked for failed legs
- **WHEN** a leg query fails
- **THEN** the `on_leg_complete` callback is invoked with `PriceCacheEntry(failed=True)` for that leg's segments

### Requirement: TicketStatus loading value
The `TicketStatus` type SHALL include a `"loading"` value indicating that ticket price data is being fetched asynchronously. The `SegmentTicketStatus` type SHALL also include `"loading"`.

#### Scenario: Loading status in schema
- **WHEN** a route is returned before pricing is complete
- **THEN** its `ticketStatus` field is `"loading"`
- **AND** each train segment's `ticketStatus` field is `"loading"`

### Requirement: get_view compatibility during streaming
The existing `GET /{search_id}/view` endpoint SHALL continue to work during an active price stream, reading available prices from Redis cache.

#### Scenario: Partial prices available during pagination
- **WHEN** a client calls `get_view` while a price stream is active
- **AND** some legs have been cached and others have not
- **THEN** routes with cached prices are returned with `ticketStatus: "ready"` or `"unavailable"`
- **AND** routes without cached prices are returned with `ticketStatus: "loading"`
