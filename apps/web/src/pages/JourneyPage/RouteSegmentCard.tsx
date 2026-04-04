
import { useState } from 'react';
import type { TrainSegment } from '@/types/route';
import { JOURNEY_LABELS } from '@/constants/labels';
import { formatPrice } from '@vistaflow/utils';

interface RouteSegmentCardProps {
  segment: TrainSegment;
}

export function RouteSegmentCard({ segment }: RouteSegmentCardProps) {
  const [stopsExpanded, setStopsExpanded] = useState(false);

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
            <span className="mx-1 text-xs text-muted">{segment.arrivalTime}</span>
          </div>
        </div>
        {segment.stops.length > 0 && (
          <button
            type="button"
            className="stop-trigger cursor-pointer border-b border-muted/30 pb-0.5 text-xs font-display uppercase tracking-widest text-muted transition-colors hover:text-white"
            onClick={() => setStopsExpanded((value) => !value)}
          >
            {JOURNEY_LABELS.viewStops(segment.stops.length)}
          </button>
        )}
      </div>

      {segment.stops.length > 0 && (
        <div className={`stops-panel mb-4${stopsExpanded ? ' expanded' : ''}`}>
          {segment.stops.map((stop) => (
            <div key={`${stop.station.code}-${stop.arrivalTime ?? stop.station.name}`} className="relative ml-[1px] border-l border-white/5 py-1.5 pl-4 text-xs text-muted">
              <div className="absolute -left-[2.5px] top-[10px] h-1 w-1 rounded-full bg-muted" />
              {stop.station.name}
              {stop.arrivalTime && <span className="ml-2 opacity-60">{stop.arrivalTime}</span>}
              {stop.stopDuration && <span className="ml-1 opacity-40">{JOURNEY_LABELS.stopDuration(stop.stopDuration)}</span>}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
        {segment.seats.map((seat) => (
          <div
            key={seat.type}
            className="flex justify-between rounded-lg p-3 text-sm font-light"
            style={{ border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}
          >
            <span>
              <span className="mr-3 text-muted">{seat.label}</span>
              {formatPrice(seat.price)}
            </span>
            <span className={seat.available ? 'time-theme-text' : ''} style={{ color: seat.available ? undefined : 'rgba(239,68,68,0.8)' }}>
              {seat.available ? seat.availabilityText ?? JOURNEY_LABELS.ticketsAvailable : JOURNEY_LABELS.soldOut}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
