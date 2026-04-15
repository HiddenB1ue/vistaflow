import { useEffect, useMemo, useRef, useState } from 'react';
import { InputBox } from '@vistaflow/ui';

const ITEM_HEIGHT = 34;
const VISIBLE_ROWS = 6;
const REPEAT_COUNT = 3;

type ActiveSegment = 'hour' | 'minute' | null;

interface TimeWheelFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function parseTime(value: string): { hour: string; minute: string } {
  if (!value || !value.includes(':')) {
    return { hour: '', minute: '' };
  }
  const [hour, minute] = value.split(':', 2);
  return { hour: hour ?? '', minute: minute ?? '' };
}

function clampSegment(raw: string, max: number): string {
  if (!raw.trim()) {
    return '';
  }
  const parsed = Number(raw);
  if (Number.isNaN(parsed)) {
    return '';
  }
  if (parsed < 0) {
    return '00';
  }
  if (parsed > max) {
    return pad(max);
  }
  return pad(parsed);
}

function buildWheelOptions(count: number): string[] {
  return Array.from({ length: count * REPEAT_COUNT }, (_, index) => pad(index % count));
}

export function TimeWheelField({ label, value, onChange }: TimeWheelFieldProps) {
  const [activeSegment, setActiveSegment] = useState<ActiveSegment>(null);
  const [hourText, setHourText] = useState('');
  const [minuteText, setMinuteText] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const hourOptions = useMemo(() => buildWheelOptions(24), []);
  const minuteOptions = useMemo(() => buildWheelOptions(60), []);

  useEffect(() => {
    const { hour, minute } = parseTime(value);
    setHourText(hour);
    setMinuteText(minute);
  }, [value]);

  useEffect(() => {
    if (!activeSegment) {
      return;
    }

    function handleClickOutside(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setActiveSegment(null);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [activeSegment]);

  useEffect(() => {
    if (!activeSegment || !listRef.current) {
      return;
    }

    const isHour = activeSegment === 'hour';
    const currentValue = isHour ? hourText || '00' : minuteText || '00';
    const base = isHour ? 24 : 60;
    const index = base + Number(currentValue);
    listRef.current.scrollTop = Math.max(0, index * ITEM_HEIGHT - ITEM_HEIGHT * 2.5);
  }, [activeSegment, hourText, minuteText]);

  const commit = (nextHour: string, nextMinute: string) => {
    if (!nextHour && !nextMinute) {
      onChange('');
      return;
    }

    const safeHour = clampSegment(nextHour || '00', 23);
    const safeMinute = clampSegment(nextMinute || '00', 59);
    onChange(`${safeHour}:${safeMinute}`);
  };

  const handleScrollLoop = (event: React.UIEvent<HTMLDivElement>, base: number) => {
    const target = event.currentTarget;
    const sectionHeight = base * ITEM_HEIGHT;
    if (target.scrollTop < sectionHeight * 0.5) {
      target.scrollTop += sectionHeight;
    } else if (target.scrollTop > sectionHeight * 1.5) {
      target.scrollTop -= sectionHeight;
    }
  };

  const currentOptions = activeSegment === 'minute' ? minuteOptions : hourOptions;
  const currentBase = activeSegment === 'minute' ? 60 : 24;
  const currentValue =
    activeSegment === 'minute' ? minuteText || '00' : hourText || '00';

  return (
    <div ref={rootRef} className="relative space-y-2">
      <label className="vf-drawer-label">{label}</label>

      <div className="flex items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-white/10 bg-black/25 px-3 py-2">
          <button
            type="button"
            className={`rounded-lg border px-2 py-1 transition ${
              activeSegment === 'hour'
                ? 'border-transparent time-theme-bg'
                : 'border-white/8 bg-white/3 hover:border-white/20'
            }`}
            style={activeSegment === 'hour' ? { color: 'var(--color-pulse-contrast)' } : undefined}
            onClick={() => setActiveSegment((current) => (current === 'hour' ? null : 'hour'))}
          >
            <InputBox
              value={hourText}
              inputMode="numeric"
              maxLength={2}
              placeholder="时"
              className="w-10 border-none bg-transparent px-0 py-0 text-center text-base tracking-[0.14em]"
              onFocus={() => setActiveSegment('hour')}
              onClick={(event) => event.stopPropagation()}
              onChange={(event) => {
                const next = event.target.value.replace(/\D/g, '').slice(0, 2);
                setHourText(next);
              }}
              onBlur={() => {
                const safeHour = clampSegment(hourText, 23);
                setHourText(safeHour);
                commit(safeHour, minuteText);
              }}
            />
          </button>

          <span className="text-sm text-muted">:</span>

          <button
            type="button"
            className={`rounded-lg border px-2 py-1 transition ${
              activeSegment === 'minute'
                ? 'border-transparent time-theme-bg'
                : 'border-white/8 bg-white/3 hover:border-white/20'
            }`}
            style={
              activeSegment === 'minute'
                ? { color: 'var(--color-pulse-contrast)' }
                : undefined
            }
            onClick={() =>
              setActiveSegment((current) => (current === 'minute' ? null : 'minute'))
            }
          >
            <InputBox
              value={minuteText}
              inputMode="numeric"
              maxLength={2}
              placeholder="分"
              className="w-10 border-none bg-transparent px-0 py-0 text-center text-base tracking-[0.14em]"
              onFocus={() => setActiveSegment('minute')}
              onClick={(event) => event.stopPropagation()}
              onChange={(event) => {
                const next = event.target.value.replace(/\D/g, '').slice(0, 2);
                setMinuteText(next);
              }}
              onBlur={() => {
                const safeMinute = clampSegment(minuteText, 59);
                setMinuteText(safeMinute);
                commit(hourText, safeMinute);
              }}
            />
          </button>
        </div>

        <button
          type="button"
          className="rounded-full border border-white/10 px-3 py-2 text-xs tracking-[0.16em] text-muted transition hover:border-white/25 hover:text-white"
          onClick={() => {
            setHourText('');
            setMinuteText('');
            setActiveSegment(null);
            onChange('');
          }}
        >
          不限
        </button>
      </div>

      {activeSegment ? (
        <div
          className={`absolute top-full z-[1200] mt-2 w-24 rounded-2xl border border-white/10 bg-[rgba(10,10,16,0.96)] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.45)] backdrop-blur-xl ${
            activeSegment === 'hour' ? 'left-0' : 'left-20'
          }`}
        >
          <div className="mb-2 text-center text-[11px] tracking-[0.18em] text-muted">
            {activeSegment === 'hour' ? '小时' : '分钟'}
          </div>
          <div
            ref={listRef}
            className="overflow-y-auto rounded-xl border border-white/8 bg-white/3"
            style={{ height: ITEM_HEIGHT * VISIBLE_ROWS }}
            onScroll={(event) => handleScrollLoop(event, currentBase)}
          >
            {currentOptions.map((option, index) => (
              <button
                key={`${activeSegment}-${index}-${option}`}
                type="button"
                className={`flex w-full items-center justify-center text-sm tracking-[0.18em] transition ${
                  currentValue === option
                    ? 'time-wheel-item-active'
                    : 'text-starlight/80 hover:bg-white/5'
                }`}
                style={{ height: ITEM_HEIGHT }}
                onClick={() => {
                  if (activeSegment === 'hour') {
                    setHourText(option);
                    commit(option, minuteText);
                  } else {
                    setMinuteText(option);
                    commit(hourText, option);
                  }
                  setActiveSegment(null);
                }}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
