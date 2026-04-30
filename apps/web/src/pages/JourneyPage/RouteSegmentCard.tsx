import { useState } from 'react';
import type { TrainSegment, TrainStop } from '@/types/route';
import { JOURNEY_LABELS } from '@/constants/labels';
import { formatPrice } from '@vistaflow/utils';
import { apiClient } from '@/services/api';
import { RouteTimeText } from './RouteTimeText';

interface RouteSegmentCardProps {
  segment: TrainSegment;
}

function getSeatAvailabilityLabel(segment: TrainSegment, seat: TrainSegment['seats'][number]): string {
  if (segment.ticketStatus === 'unavailable') {
    return JOURNEY_LABELS.ticketsUnavailable;
  }
  if (segment.ticketStatus === 'disabled') {
    return JOURNEY_LABELS.ticketsNotQueried;
  }
  if (seat.available) {
    return seat.availabilityText ?? JOURNEY_LABELS.ticketsAvailable;
  }
  return JOURNEY_LABELS.soldOut;
}

function getSeatPriceLabel(seat: TrainSegment['seats'][number]): string {
  return seat.price === null ? '--' : formatPrice(seat.price);
}

export function RouteSegmentCard({ segment }: RouteSegmentCardProps) {
  const [stopsExpanded, setStopsExpanded] = useState(false);
  const [stops, setStops] = useState<TrainStop[]>(segment.stops);
  const [isLoadingStops, setIsLoadingStops] = useState(false);

  const displayStopsCount = segment.stopsCount ?? stops.length;

  const handleToggleStops = async () => {
    if (!stopsExpanded && stops.length === 0) {
      setIsLoadingStops(true);
      try {
        const { data } = await apiClient.get<{
          data: {
            train_code: string;
            stops: Array<{
              station_name: string;
              arrival_time: string | null;
              departure_time: string | null;
              stop_number: number;
            }>;
          };
        }>(
          `/trains/${segment.no}/stops?from_station=${encodeURIComponent(segment.origin.name)}&to_station=${encodeURIComponent(segment.destination.name)}&full_route=true`,
        );

        const trainStops: TrainStop[] = data.data.stops.map((stop) => ({
          station: {
            name: stop.station_name,
            code: '',
            city: '',
            lng: 0,
            lat: 0,
          },
          arrivalTime: stop.arrival_time,
          departureTime: stop.departure_time,
          stopDuration: null,
        }));

        setStops(trainStops);
      } catch (error) {
        console.error('Failed to fetch train stops:', error);
      } finally {
        setIsLoadingStops(false);
      }
    }
    setStopsExpanded((value) => !value);
  };

  return (
    <div className="relative mb-2 ml-[3px] border-l border-white/10 py-4 pl-6">
      <div
        className="absolute -left-[4.5px] top-6 h-2 w-2 rounded-full bg-starlight"
        style={{ boxShadow: '0 0 8px rgba(255,255,255,0.4)' }}
      />

      <div className="mb-4 flex items-end justify-between pr-2">
        <div>
          <div className="mb-1 font-display text-lg text-starlight">{segment.no}</div>
          <div className="text-sm font-light tracking-wide text-starlight">
            {segment.origin.name}
            <span className="mx-1 text-xs text-muted">{segment.departureTime}</span>
            <span className="mx-1 text-muted">→</span>
            {segment.destination.name}
            <RouteTimeText
              date={segment.arrivalDate}
              time={segment.arrivalTime}
              baseDate={segment.departureDate}
              className="mx-1 text-xs text-muted"
            />
          </div>
        </div>
        <button
          type="button"
          className="stop-trigger cursor-pointer border-b border-muted/30 pb-0.5 text-xs font-display uppercase tracking-widest text-muted transition-colors hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          onClick={handleToggleStops}
          disabled={isLoadingStops}
        >
          {isLoadingStops ? JOURNEY_LABELS.loading : JOURNEY_LABELS.viewStops(displayStopsCount)}
        </button>
      </div>

      {stops.length > 0 && (
        <div className={`stops-panel mb-4${stopsExpanded ? ' expanded' : ''}`}>
          {stops.map((stop, index) => {
            const isFirstStop = index === 0;
            const displayTime = isFirstStop ? stop.departureTime : stop.arrivalTime;
            const originIndex = stops.findIndex((item) => item.station.name === segment.origin.name);
            const destinationIndex = stops.findIndex((item) => item.station.name === segment.destination.name);
            const isInCurrentSegment =
              stop.station.name === segment.origin.name ||
              stop.station.name === segment.destination.name ||
              (originIndex !== -1 && destinationIndex !== -1 && originIndex <= index && index <= destinationIndex);

            return (
              <div
                key={`${stop.station.name}-${index}`}
                className={`relative ml-[1px] border-l border-white/5 py-1.5 pl-4 text-xs ${
                  isInCurrentSegment ? 'text-starlight' : 'text-muted opacity-40'
                }`}
              >
                <div
                  className={`absolute -left-[2.5px] top-[10px] h-1 w-1 rounded-full ${
                    isInCurrentSegment ? 'bg-starlight' : 'bg-muted'
                  }`}
                />
                {stop.station.name}
                {displayTime && (
                  <span className={`ml-2 ${isInCurrentSegment ? 'opacity-80' : 'opacity-40'}`}>
                    {displayTime}
                  </span>
                )}
                {stop.stopDuration && <span className="ml-1 opacity-40">{JOURNEY_LABELS.stopDuration(stop.stopDuration)}</span>}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
        {segment.ticketStatus === 'ready' && segment.seats.length === 0 ? (
          <div
            className="flex justify-between rounded-lg p-3 text-sm font-light"
            style={{ border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}
          >
            <span className="text-muted">{JOURNEY_LABELS.noSeatInfo}</span>
          </div>
        ) : (
          segment.seats.map((seat) => (
            <div
              key={`${seat.type}-${seat.label}`}
              className="flex justify-between rounded-lg p-3 text-sm font-light"
              style={{ border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}
            >
              <span>
                <span className="mr-3 text-muted">{seat.label}</span>
                {getSeatPriceLabel(seat)}
              </span>
              <span
                className={seat.available ? 'time-theme-text' : ''}
                style={{ color: seat.available ? undefined : 'rgba(239,68,68,0.8)' }}
              >
                {getSeatAvailabilityLabel(segment, seat)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
