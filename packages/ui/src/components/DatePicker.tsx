import { useEffect, useMemo, useState } from 'react';
import { Button } from './Button';
import { ModalBody, ModalFooter, ModalHeader, ModalShell } from './Modal';

export type DatePickerAppearance = 'boxed' | 'hero';

interface DatePreset {
  label: string;
  offsetDays: number;
}

export interface DatePickerLabels {
  selectedDateEyebrow: string;
  prevMonthAriaLabel: string;
  nextMonthAriaLabel: string;
  monthSuffix: string;
  yearSuffix: string;
  closeLabel: string;
  weekdays: [string, string, string, string, string, string, string];
}

export interface DatePickerProps {
  value: string;
  onChange: (value: string) => void;
  appearance?: DatePickerAppearance;
  className?: string;
  minDate?: Date;
  presets?: ReadonlyArray<DatePreset>;
  labels?: Partial<DatePickerLabels>;
}

const DEFAULT_LABELS: DatePickerLabels = {
  selectedDateEyebrow: '已选日期',
  prevMonthAriaLabel: '上一月',
  nextMonthAriaLabel: '下一月',
  monthSuffix: '月',
  yearSuffix: '年',
  closeLabel: '关闭日期选择器',
  weekdays: ['日', '一', '二', '三', '四', '五', '六'],
};

const DEFAULT_PRESETS: DatePreset[] = [
  { label: '今天', offsetDays: 0 },
  { label: '明天', offsetDays: 1 },
  { label: '一周后', offsetDays: 7 },
];

function normalizeDate(input: Date): Date {
  const normalized = new Date(input);
  normalized.setHours(0, 0, 0, 0);
  return normalized;
}

function formatLabel(date: Date): string {
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function formatISO(date: Date): string {
  // Use local date components to avoid timezone conversion issues
  // This ensures the date stays consistent regardless of user's timezone
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseDateValue(value: string, reference: Date, minimumDate: Date): Date | null {
  const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    const year = Number(isoMatch[1]);
    const month = Number(isoMatch[2]) - 1;
    const day = Number(isoMatch[3]);
    const candidate = normalizeDate(new Date(year, month, day));
    return Number.isNaN(candidate.getTime()) ? null : candidate;
  }

  const labelMatch = value.match(/^(\d{1,2})月(\d{1,2})日$/);
  if (!labelMatch) return null;

  const month = Number(labelMatch[1]) - 1;
  const day = Number(labelMatch[2]);
  let candidate = normalizeDate(new Date(reference.getFullYear(), month, day));

  if (Number.isNaN(candidate.getTime())) return null;

  if (candidate < minimumDate) {
    candidate = normalizeDate(new Date(reference.getFullYear() + 1, month, day));
  }

  return candidate;
}

export function DatePicker({
  value,
  onChange,
  appearance = 'boxed',
  className = '',
  minDate,
  presets = DEFAULT_PRESETS,
  labels,
}: DatePickerProps) {
  const resolvedLabels = useMemo(() => ({ ...DEFAULT_LABELS, ...labels }), [labels]);
  const today = useMemo(() => normalizeDate(new Date()), []);
  const minimumDate = useMemo(() => normalizeDate(minDate ?? today), [minDate, today]);
  const resolvedInitialDate = useMemo(
    () => parseDateValue(value, today, minimumDate) ?? today,
    [minimumDate, today, value],
  );

  const [isOpen, setIsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date>(resolvedInitialDate);
  const [pickerDate, setPickerDate] = useState<Date>(resolvedInitialDate);

  useEffect(() => {
    const parsed = parseDateValue(value, today, minimumDate);
    if (parsed) {
      setSelectedDate(parsed);
      setPickerDate(parsed);
      return;
    }

    if (!value) {
      onChange(formatISO(today));
    }
  }, [minimumDate, onChange, today, value]);

  const displayLabel = formatLabel(selectedDate);
  const year = pickerDate.getFullYear();
  const month = pickerDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const triggerClassName = useMemo(() => {
    const base = appearance === 'hero'
      ? 'vf-date-trigger vf-date-trigger--hero'
      : 'vf-date-trigger vf-date-trigger--boxed';

    return `${base} ${className}`.trim();
  }, [appearance, className]);

  const close = () => setIsOpen(false);

  const selectDate = (yearValue: number, monthValue: number, dayValue: number) => {
    const nextDate = normalizeDate(new Date(yearValue, monthValue, dayValue));
    if (nextDate < minimumDate) return;

    setSelectedDate(nextDate);
    setPickerDate(nextDate);
    onChange(formatISO(nextDate));
    close();
  };

  const selectPreset = (offsetDays: number) => {
    const nextDate = normalizeDate(new Date(today));
    nextDate.setDate(nextDate.getDate() + offsetDays);

    setSelectedDate(nextDate);
    setPickerDate(nextDate);
    onChange(formatISO(nextDate));
    close();
  };

  const modal = isOpen ? (
    <ModalShell open size="sm" className="vf-date-picker-shell" onBackdropClick={close}>
      <ModalHeader
        eyebrow={resolvedLabels.selectedDateEyebrow}
        title={displayLabel}
        subtitle={`${year}${resolvedLabels.yearSuffix}`}
        onClose={close}
        closeLabel={resolvedLabels.closeLabel}
      />

      <ModalBody className="vf-date-picker-body">
        <div className="vf-calendar__toolbar">
          <button
            type="button"
            aria-label={resolvedLabels.prevMonthAriaLabel}
            className="vf-calendar__nav"
            onClick={() => setPickerDate((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1))}
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div className="vf-calendar__month">{month + 1}{resolvedLabels.monthSuffix}</div>

          <button
            type="button"
            aria-label={resolvedLabels.nextMonthAriaLabel}
            className="vf-calendar__nav"
            onClick={() => setPickerDate((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1))}
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div className="vf-calendar__weekday-row">
          {resolvedLabels.weekdays.map((day) => <div key={day}>{day}</div>)}
        </div>

        <div className="vf-calendar__grid">
          {Array.from({ length: firstDay }, (_, index) => (
            <div key={`empty-${index}`} className="vf-calendar__day vf-calendar__day--empty" />
          ))}

          {Array.from({ length: daysInMonth }, (_, index) => {
            const day = index + 1;
            const loopDate = normalizeDate(new Date(year, month, day));
            const selected =
              selectedDate.getDate() === day &&
              selectedDate.getMonth() === month &&
              selectedDate.getFullYear() === year;
            const disabled = loopDate < minimumDate;

            return (
              <button
                key={day}
                type="button"
                className={`vf-calendar__day${selected ? ' vf-calendar__day--active' : ''}${disabled ? ' vf-calendar__day--disabled' : ''}`.trim()}
                onClick={() => selectDate(year, month, day)}
                disabled={disabled}
              >
                {day}
              </button>
            );
          })}
        </div>
      </ModalBody>

      <ModalFooter align="start" className="vf-date-picker-footer">
        {presets.map((preset) => (
          <Button
            key={preset.label}
            variant="outline"
            className="vf-date-picker-preset"
            onClick={() => selectPreset(preset.offsetDays)}
          >
            {preset.label}
          </Button>
        ))}
      </ModalFooter>
    </ModalShell>
  ) : null;

  return (
    <>
      <button
        type="button"
        className={triggerClassName}
        onClick={() => {
          setPickerDate(selectedDate);
          setIsOpen(true);
        }}
      >
        {displayLabel}
      </button>
      {modal}
    </>
  );
}
