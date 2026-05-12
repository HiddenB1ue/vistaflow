import type { JourneySearchSessionResult } from '@/services/routeService';
import { useSearchProgressStore } from '@/stores/searchProgressStore';
import type { SearchParams } from '@/types/search';
import { buildJourneyViewRequest } from '@/services/routeService';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

function normalizeStationName(name: string): string {
  return name.endsWith('站') ? name.slice(0, -1) : name;
}

/**
 * Start an SSE session creation stream. Updates searchProgressStore in
 * real-time and returns the final session result on completion.
 *
 * Throws on network errors or if the backend sends an error event.
 */
export async function createSessionStream(
  params: SearchParams,
): Promise<JourneySearchSessionResult> {
  const { applyEvent, start } = useSearchProgressStore.getState();
  start();

  const initialView = buildJourneyViewRequest(
    {
      excludeDirectTrainCodesInTransferRoutes: false,
      displayTrainTypes: [],
      transferCounts: [],
      showOnlyAvailableTickets: false,
    },
    'duration',
    1,
    20,
  );

  const response = await fetch(`${API_BASE}/journey-search-sessions/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_station: normalizeStationName(params.origin),
      to_station: normalizeStationName(params.destination),
      date: params.date,
      transfer_count: params.transferCount,
      include_fewer_transfers: true,
      allowed_train_types: params.allowedTrainTypes,
      excluded_train_types: params.excludedTrainTypes,
      allowed_trains: params.allowedTrains,
      excluded_trains: params.excludedTrains,
      departure_time_start: params.departureTimeStart || undefined,
      departure_time_end: params.departureTimeEnd || undefined,
      arrival_deadline: params.arrivalDeadline || undefined,
      min_transfer_minutes: params.minTransferMinutes,
      max_transfer_minutes: params.maxTransferMinutes
        ? Number(params.maxTransferMinutes)
        : undefined,
      allowed_transfer_stations: params.allowedTransferStations,
      excluded_transfer_stations: params.excludedTransferStations,
      filter_running_only: true,
      view: initialView,
    }),
  });

  if (!response.ok) {
    applyEvent({ type: 'error', message: `HTTP ${response.status}` });
    throw new Error(`Session stream failed: HTTP ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    applyEvent({ type: 'error', message: '浏览器不支持流式响应' });
    throw new Error('ReadableStream not available');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let sessionResult: JourneySearchSessionResult | null = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      // Keep the last (possibly incomplete) line in the buffer
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const jsonStr = trimmed.slice(5).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr) as Record<string, unknown>;
          applyEvent(event);

          if (event.type === 'complete' && event.data) {
            sessionResult = event.data as JourneySearchSessionResult;
          }

          if (event.type === 'error') {
            throw new Error(
              (event.message as string) ?? '搜索失败，请稍后重试',
            );
          }
        } catch (parseErr) {
          if (parseErr instanceof Error && parseErr.message.includes('搜索失败')) {
            throw parseErr;
          }
          // Ignore malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  if (!sessionResult) {
    applyEvent({ type: 'error', message: '未收到完整搜索结果' });
    throw new Error('Stream ended without complete event');
  }

  return sessionResult;
}
