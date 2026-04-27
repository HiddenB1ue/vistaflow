import { useEffect, useMemo } from 'react';
import { DatePicker, type DatePickerAppearance, type DatePickerLabels } from './DatePicker';
import { NumberWheel } from './NumberWheel';

export interface DateTimePickerProps {
  value: string;
  onChange: (value: string) => void;
  appearance?: DatePickerAppearance;
  className?: string;
  minDate?: Date;
  minuteStep?: number;
  labels?: Partial<DatePickerLabels>;
}

export interface DateTimeParts {
  date: string;
  hour: string;
  minute: string;
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function formatLocalDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function normalizeMinute(minute: number, minuteStep: number): number {
  return Math.floor(minute / minuteStep) * minuteStep;
}

export function parseDateTimeValue(
  value: string,
  options: { fallback?: Date; minuteStep?: number } = {},
): DateTimeParts {
  const fallback = options.fallback ?? new Date();
  const minuteStep = options.minuteStep ?? 1;
  const parsed = value ? new Date(value) : null;
  const source = parsed && !Number.isNaN(parsed.getTime()) ? parsed : fallback;
  const minute = normalizeMinute(source.getMinutes(), minuteStep);

  return {
    date: formatLocalDate(source),
    hour: pad(source.getHours()),
    minute: pad(minute),
  };
}

export function buildDateTimeISOString(parts: DateTimeParts): string {
  const parsed = new Date(`${parts.date}T${parts.hour}:${parts.minute}:00`);
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toISOString();
}

export function DateTimePicker({
  value,
  onChange,
  appearance = 'boxed',
  className = '',
  minDate,
  minuteStep = 1,
  labels,
}: DateTimePickerProps) {
  const parts = useMemo(
    () => parseDateTimeValue(value, { minuteStep }),
    [minuteStep, value],
  );

  useEffect(() => {
    if (!value) {
      onChange(buildDateTimeISOString(parts));
    }
  }, [onChange, parts, value]);

  const update = (patch: Partial<DateTimeParts>) => {
    onChange(buildDateTimeISOString({ ...parts, ...patch }));
  };

  return (
    <div className={`vf-date-time-picker ${className}`.trim()}>
      <DatePicker
        value={parts.date}
        onChange={(date) => update({ date })}
        appearance={appearance}
        minDate={minDate}
        labels={labels}
      />
      <div className="vf-date-time-picker__time">
        <NumberWheel
          value={Number(parts.hour)}
          min={0}
          max={23}
          onChange={(hour) => update({ hour: pad(hour) })}
          label="时"
          className="vf-date-time-picker__wheel"
        />
        <NumberWheel
          value={Number(parts.minute)}
          min={0}
          max={60 - minuteStep}
          step={minuteStep}
          onChange={(minute) => update({ minute: pad(minute) })}
          label="分"
          className="vf-date-time-picker__wheel"
        />
      </div>
    </div>
  );
}
