from __future__ import annotations

SYSTEM_SETTING_CACHE_TTL_SECONDS = 5.0

SYSTEM_SETTING_KEYS = frozenset(
    {
        "amap_api_key",
        "amap_max_retries",
        "amap_retry_delay_seconds",
        "amap_min_interval_seconds",
        "amap_rate_limit_cooldown_seconds",
        "ticket_12306_cookie",
        "geo_enrich_enabled",
        "auto_crawl_enabled",
        "price_sync_enabled",
        "maintenance_mode",
        "preview_write_enabled",
    }
)

TOGGLE_SETTING_KEYS = frozenset(
    {
        "geo_enrich_enabled",
        "auto_crawl_enabled",
        "price_sync_enabled",
        "maintenance_mode",
        "preview_write_enabled",
    }
)

OPTIONAL_STRING_SETTING_KEYS = frozenset({"amap_api_key", "ticket_12306_cookie"})
