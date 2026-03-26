import { useState } from 'react';
import type { Route, TrainSegment } from '@/types/route';
import { isTransfer } from '@/types/route';
import { formatDuration } from '@/utils/duration';
import { formatPrice } from '@/utils/price';
import { getLowestAvailablePrice } from '@/utils/seat';

interface RouteCardProps {
  route: Route;
  isActive: boolean;
  onClick: (route: Route) => void;
}

function TrainSegCard({ seg }: { seg: TrainSegment }) {
  const [stopsExpanded, setStopsExpanded] = useState(false);

  return (
    <div className="relative pl-6 py-4 border-l border-white/10 ml-[3px] mb-2">
      {/* 左侧白点 */}
      <div
        className="absolute w-2 h-2 rounded-full -left-[4.5px] top-6 bg-starlight"
        style={{ boxShadow: '0 0 8px rgba(255,255,255,0.4)' }}
      />

      {/* 车次 + 出发/到达 */}
      <div className="flex items-end justify-between mb-4 pr-2">
        <div>
          <div className="font-display text-lg mb-1 text-starlight">
            {seg.no}
          </div>
          <div className="text-sm font-light tracking-wide text-starlight">
            {seg.origin.name}
            <span className="text-xs mx-1 text-muted">{seg.departureTime}</span>
            <span className="mx-1 text-muted">→</span>
            {seg.destination.name}
            <span className="text-xs mx-1 text-muted">{seg.arrivalTime}</span>
          </div>
        </div>
        {seg.stops.length > 0 && (
          <div
            className="stop-trigger text-xs font-display tracking-widest uppercase cursor-pointer transition-colors hover:text-white pb-0.5 text-muted border-b border-muted/30"
            onClick={() => setStopsExpanded((v) => !v)}
          >
            查看 {seg.stops.length} 个经停站
          </div>
        )}
      </div>

      {/* 经停站面板 */}
      {seg.stops.length > 0 && (
        <div className={`stops-panel mb-4${stopsExpanded ? ' expanded' : ''}`}>
          {seg.stops.map((stop) => (
            <div
              key={stop.station.code}
              className="text-xs text-muted py-1.5 relative pl-4 border-l border-white/5 ml-[1px]"
            >
              <div className="absolute w-1 h-1 bg-muted rounded-full -left-[2.5px] top-[10px]" />
              {stop.station.name}
              {stop.arrivalTime && (
                <span className="opacity-60 ml-2">{stop.arrivalTime}</span>
              )}
              {stop.stopDuration && (
                <span className="opacity-40 ml-1">- 停留 {stop.stopDuration} 分钟</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 座位网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        {seg.seats.map((seat) => (
          <div
            key={seat.type}
            className="flex justify-between p-3 rounded-lg text-sm font-light"
            style={{
              border: '1px solid rgba(255,255,255,0.05)',
              background: 'rgba(0,0,0,0.2)',
            }}
          >
            <span>
              <span className="text-muted mr-3">{seat.label}</span>
              ¥{seat.price}
            </span>
            <span
              style={{ color: seat.available ? undefined : 'rgba(239,68,68,0.8)' }}
              className={seat.available ? 'time-theme-text' : ''}
            >
              {seat.available ? (seat.availabilityText ?? '充足') : '已售罄'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RouteCard({ route, isActive, onClick }: RouteCardProps) {
  const allSeats = route.segs.flatMap((s) => (isTransfer(s) ? [] : s.seats));
  const lowestPrice = getLowestAvailablePrice(allSeats);
  const displayPrice = lowestPrice !== null ? formatPrice(lowestPrice) : '已售罄';

  return (
    <div
      data-card
      className={`ticket-card cursor-pointer${isActive ? ' active' : ''}`}
      onClick={() => onClick(route)}
    >
      {/* ===== 卡片头部 ===== */}
      <div className="flex justify-between items-start pr-4">
        <div>
          <div className="text-xs time-theme-text font-display tracking-[0.2em] uppercase mb-3">
            {route.type} • {formatDuration(route.durationMinutes)}
          </div>
          <div className="font-serif text-3xl md:text-4xl font-light tracking-wide text-starlight">
            {route.departureTime}
            <span className="font-sans text-xl px-3 font-light text-muted"> → </span>
            {route.arrivalTime}
          </div>
        </div>
        <div className="text-right">
          <div className="font-display text-2xl md:text-3xl font-light tracking-wider text-starlight">
            {displayPrice}
          </div>
          {lowestPrice !== null && (
            <div className="text-xs text-muted/80 font-medium tracking-widest uppercase mt-1">
              参考起价
            </div>
          )}
        </div>
      </div>

      {/* ===== 展开详情面板：CSS max-height 过渡 ===== */}
      <div className="details-panel pl-2 md:pl-6 mt-4" onClick={(e) => e.stopPropagation()}>
        {route.segs.map((seg, i) =>
          isTransfer(seg) ? (
            <div
              key={`transfer-${i}`}
              className="py-6 flex items-center gap-6 text-sm font-display tracking-wider time-theme-text opacity-80"
            >
              <div className="w-1.5 h-1.5 rounded-full border border-current" />
              <span>{seg.transfer}</span>
              <div
                className="h-px flex-1"
                style={{ background: 'linear-gradient(to right, currentColor, transparent)', opacity: 0.2 }}
              />
            </div>
          ) : (
            <TrainSegCard key={`seg-${i}`} seg={seg} />
          )
        )}

        {/* 底部：免责声明 + 购票按钮 */}
        <div
          className="mt-8 pt-6 flex flex-col md:flex-row items-center justify-between gap-4"
          style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
        >
          <div className="font-light leading-relaxed text-[11px] text-muted">
            VistaFlow 仅提供行程规划参考，<br />
            实际购票请前往官方渠道。
          </div>
          <button
            className="book-btn hover-time-theme bg-starlight text-void px-6 py-3 rounded-full text-xs font-bold tracking-[0.1em] transition-all w-full md:w-auto flex items-center justify-center gap-2 cursor-pointer"
            onClick={() => window.open('https://www.12306.cn', '_blank')}
          >
            前往 12306 购票
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
