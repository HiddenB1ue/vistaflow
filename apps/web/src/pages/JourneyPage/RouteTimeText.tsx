import { getRouteDayOffset } from '@/utils/dateTime';

interface RouteTimeTextProps {
  date: string;
  time: string;
  baseDate: string;
  className?: string;
}

export function RouteTimeText({ date, time, baseDate, className }: RouteTimeTextProps) {
  const dayOffset = getRouteDayOffset(date, baseDate);

  return (
    <span className={className}>
      {time}
      {dayOffset > 0 ? (
        <sup className="route-time-offset">+{dayOffset}</sup>
      ) : null}
    </span>
  );
}
