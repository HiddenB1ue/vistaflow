import type { PriceCacheEntry } from '@/stores/priceStore';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

export interface PriceStreamCallbacks {
  onStarted: (totalLegs: number, cachedLegs: number, legsToFetch: number) => void;
  onPriceBatch: (prices: Record<string, PriceCacheEntry>) => void;
  onLegFetched: (completed: number, total: number) => void;
  onComplete: () => void;
  onError: (message: string) => void;
}

/**
 * Open an SSE connection to the price stream endpoint.
 * Returns an abort function to cancel the stream.
 */
export function startPriceStream(
  searchId: string,
  callbacks: PriceStreamCallbacks,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(
        `${API_BASE}/journey-search-sessions/${encodeURIComponent(searchId)}/prices/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
        },
      );

      if (!response.ok) {
        callbacks.onError(`HTTP ${response.status}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError('ReadableStream not available');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;
            const jsonStr = trimmed.slice(5).trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr) as Record<string, unknown>;

              switch (event.type) {
                case 'pricing_started':
                  callbacks.onStarted(
                    event.totalLegs as number,
                    event.cachedLegs as number,
                    event.legsToFetch as number,
                  );
                  break;
                case 'leg_priced':
                  callbacks.onPriceBatch(
                    event.prices as Record<string, PriceCacheEntry>,
                  );
                  break;
                case 'leg_fetched':
                  callbacks.onLegFetched(
                    event.completed as number,
                    event.total as number,
                  );
                  break;
                case 'pricing_complete':
                  callbacks.onComplete();
                  break;
                case 'error':
                  callbacks.onError(
                    (event.message as string) ?? 'Price stream error',
                  );
                  break;
              }
            } catch {
              // Ignore malformed SSE lines
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return; // Expected when stream is aborted
      }
      callbacks.onError(err instanceof Error ? err.message : 'Price stream failed');
    }
  })();

  return () => controller.abort();
}
