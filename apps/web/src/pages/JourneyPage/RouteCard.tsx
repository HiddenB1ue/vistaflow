
import './RouteCard.css';
import type { Route } from '@/types/route';
import { isTransfer } from '@/types/route';
import { JOURNEY_LABELS } from '@/constants/labels';
import { formatDuration, formatPrice } from '@vistaflow/utils';
import { getRouteReferencePrice } from '@/utils/seat';
import { formatRouteDateTime } from '@/utils/dateTime';
import { RouteSegmentCard } from './RouteSegmentCard';
import { getCollapsedRouteSummary } from './routeList.helpers';

interface RouteCardProps {
  route: Route;
  isActive: boolean;
  onClick: (route: Route) => void;
}

function getRoutePriceLabel(route: Route): string {
  const referencePrice = getRouteReferencePrice(route);

  if (referencePrice !== null) {
    return formatPrice(referencePrice);
  }
  if (route.ticketStatus === 'unavailable' || route.ticketStatus === 'partial') {
    return JOURNEY_LABELS.ticketsUnavailable;
  }
  if (route.ticketStatus === 'disabled') {
    return JOURNEY_LABELS.ticketsNotQueried;
  }
  return JOURNEY_LABELS.soldOut;
}

export function RouteCard({ route, isActive, onClick }: RouteCardProps) {
  const referencePrice = getRouteReferencePrice(route);
  const displayPrice = getRoutePriceLabel(route);
  const collapsedSummary = getCollapsedRouteSummary(route);

  return (
    <div data-card className={`ticket-card cursor-pointer${isActive ? ' active' : ''}`} onClick={() => onClick(route)}>
      <div className="flex items-start justify-between gap-6 pr-4">
        <div className="min-w-0 flex-1">
          <div className="mb-3 font-display text-xs uppercase tracking-[0.2em] time-theme-text">
            {route.type} · {formatDuration(route.durationMinutes)}
          </div>
          <div className="font-serif text-3xl font-light tracking-wide text-starlight md:text-4xl">
            {route.departureTime}
            <span className="px-3 font-sans text-xl font-light text-muted">→</span>
            {formatRouteDateTime(route.arrivalDate, route.arrivalTime, route.departureDate)}
          </div>
          <div className="route-card-summary mt-4">
            <div className="route-card-summary__row route-card-summary__row--train-codes">
              {collapsedSummary.trainCodes.map((trainCode) => (
                <span key={trainCode} className="route-card-summary__badge route-card-summary__badge--train">
                  {trainCode}
                </span>
              ))}
            </div>
            {collapsedSummary.kind === 'direct' && collapsedSummary.endpoints ? (
              <div className="route-card-summary__row">
                <span className="route-card-summary__meta">{collapsedSummary.endpoints}</span>
              </div>
            ) : null}
            {collapsedSummary.kind === 'transfer' && collapsedSummary.transferStations.length > 0 ? (
              <div className="route-card-summary__row route-card-summary__row--transfer-stations">
                {collapsedSummary.transferStations.map((transferStation) => (
                  <span key={transferStation} className="route-card-summary__badge route-card-summary__badge--transfer">
                    {transferStation}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="font-display text-2xl font-light tracking-wider text-starlight md:text-3xl">{displayPrice}</div>
          {referencePrice !== null && (
            <div className="mt-1 text-xs font-medium uppercase tracking-widest text-muted/80">
              {JOURNEY_LABELS.referencePrice}
            </div>
          )}
        </div>
      </div>

      <div className="details-panel mt-4 pl-2 md:pl-6" onClick={(event) => event.stopPropagation()}>
        {route.segs.map((segment, index) => (
          isTransfer(segment) ? (
            <div key={`transfer-${index}`} className="flex items-center gap-6 py-6 text-sm font-display tracking-wider time-theme-text opacity-80">
              <div className="h-1.5 w-1.5 rounded-full border border-current" />
              <span>{segment.transfer}</span>
              <div className="h-px flex-1" style={{ background: 'linear-gradient(to right, currentColor, transparent)', opacity: 0.2 }} />
            </div>
          ) : (
            <RouteSegmentCard key={`segment-${index}`} segment={segment} />
          )
        ))}

        <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-white/[0.05] pt-6 md:flex-row">
          <div className="text-[11px] font-light leading-relaxed text-muted">
            {JOURNEY_LABELS.disclaimerLine1}
            <br />
            {JOURNEY_LABELS.disclaimerLine2}
          </div>
          <button
            type="button"
            className="book-btn hover-time-theme flex w-full cursor-pointer items-center justify-center gap-2 rounded-full bg-starlight px-6 py-3 text-xs font-bold tracking-[0.1em] text-void transition-all md:w-auto"
            onClick={() => window.open('https://www.12306.cn', '_blank', 'noopener,noreferrer')}
          >
            {JOURNEY_LABELS.bookButton}
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
