import { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  animateDatePickerOpen,
  animateDatePickerClose,
  animateDatePickerMonth,
} from '@/animations/datePicker';

interface DatePickerProps {
  value: string;
  onChange: (value: string) => void;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function formatLabel(d: Date): string {
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export function DatePicker({ value, onChange }: DatePickerProps) {
  const today = useRef<Date>((() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; })()).current;
  const [isOpen, setIsOpen] = useState(false);
  const [pickerDate, setPickerDate] = useState(() => new Date(today));
  const [selectedDate, setSelectedDate] = useState<Date>(() => new Date(today));
  const overlayRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const daysRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!value) onChange(formatLabel(today));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const open = useCallback(() => {
    setPickerDate(new Date(selectedDate));
    setIsOpen(true);
  }, [selectedDate]);

  const close = useCallback(() => {
    const overlay = overlayRef.current;
    const modal = modalRef.current;
    if (!overlay || !modal) { setIsOpen(false); return; }
    animateDatePickerClose(overlay, modal, () => setIsOpen(false));
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const overlay = overlayRef.current;
    const modal = modalRef.current;
    if (!overlay || !modal) return;
    animateDatePickerOpen(overlay, modal);
  }, [isOpen]);

  const changeMonth = useCallback((dir: -1 | 1) => {
    const days = daysRef.current;
    if (!days) {
      setPickerDate(d => { const n = new Date(d); n.setMonth(n.getMonth() + dir); return n; });
      return;
    }
    animateDatePickerMonth(days, dir, () => {
      setPickerDate((d: Date) => { const n = new Date(d); n.setMonth(n.getMonth() + dir); return n; });
    });
  }, []);

  const selectDate = useCallback((year: number, month: number, day: number) => {
    const d = new Date(year, month, day);
    setSelectedDate(d);
    onChange(formatLabel(d));
    setTimeout(close, 120);
  }, [onChange, close]);

  const quickSelect = useCallback((offsetDays: number) => {
    const d = new Date(today);
    d.setDate(d.getDate() + offsetDays);
    setSelectedDate(d);
    setPickerDate(new Date(d));
    onChange(formatLabel(d));
    setTimeout(close, 120);
  }, [today, onChange, close]);

  const year = pickerDate.getFullYear();
  const month = pickerDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const displayLabel = value || formatLabel(today);

  return (
    <>
      <span
        className="nl-input date-input mx-4 cursor-pointer select-none"
        onClick={open}
      >
        {displayLabel}
      </span>

      {isOpen && createPortal(
        <div
          ref={overlayRef}
          className="fixed inset-0 flex items-center justify-center"
          style={{
            zIndex: 9000,
            opacity: 0,
            backgroundColor: 'var(--color-overlay-bg)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
          onClick={(e) => { if (e.target === overlayRef.current) close(); }}
        >
          <div
            ref={modalRef}
            className="relative overflow-hidden border border-white/10 rounded-[2rem] shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8)] w-[420px]"
            style={{ background: 'var(--color-modal-bg)', backdropFilter: 'blur(40px)', WebkitBackdropFilter: 'blur(40px)' }}
          >
            <div
              className="absolute inset-0 z-0 pointer-events-none opacity-40"
              style={{ background: 'radial-gradient(circle at 50% 0%, var(--path-color) 0%, transparent 60%)' }}
            />

            <div className="relative z-10 p-8">
              <div className="flex items-end justify-between mb-8 border-b border-white/10 pb-6">
                <div>
                  <div className="text-[10px] text-muted font-display tracking-[0.3em] uppercase mb-2">Selected Date</div>
                  <div className="font-serif italic text-4xl text-starlight">{displayLabel}</div>
                </div>
                <div className="font-display text-xl font-light" style={{ color: 'var(--color-text-secondary)' }}>{selectedDate.getFullYear()}</div>
              </div>

              <div className="flex justify-between items-center mb-6 px-1">
                <button
                  onClick={() => changeMonth(-1)}
                  aria-label="上个月"
                  className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-300 group cursor-pointer"
                >
                  <svg className="w-4 h-4 text-muted group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <div className="font-display text-base tracking-[0.2em] text-starlight uppercase font-medium">
                  {month + 1} 月
                </div>
                <button
                  onClick={() => changeMonth(1)}
                  aria-label="下个月"
                  className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-300 group cursor-pointer"
                >
                  <svg className="w-4 h-4 text-muted group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-7 gap-2 text-center text-[10px] text-muted font-display tracking-widest uppercase mb-3">
                {WEEKDAYS.map(d => <div key={d}>{d}</div>)}
              </div>

              <div className="relative h-[240px] overflow-hidden">
                <div ref={daysRef} className="absolute w-full grid grid-cols-7 gap-y-2 gap-x-2 text-center font-display text-sm text-muted">
                  {Array.from({ length: firstDay }, (_, i) => (
                    <div key={`e${i}`} className="calendar-day" />
                  ))}
                  {Array.from({ length: daysInMonth }, (_, i) => {
                    const day = i + 1;
                    const loopDate = new Date(year, month, day);
                    const isSelected = selectedDate.getDate() === day && selectedDate.getMonth() === month && selectedDate.getFullYear() === year;
                    const isPast = loopDate < today;
                    return (
                      <div
                        key={day}
                        className={`calendar-day cursor-pointer${isSelected ? ' active' : ''}${isPast && !isSelected ? ' opacity-30' : ''}`}
                        onClick={() => selectDate(year, month, day)}
                      >
                        {day}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="mt-2 pt-6 border-t border-white/10 flex gap-3">
                {([{ label: '今天', offset: 0 }, { label: '明天', offset: 1 }, { label: '下周', offset: 7 }] as const).map(({ label, offset }) => (
                  <button
                    key={label}
                    onClick={() => quickSelect(offset)}
                    className="flex-1 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-xs font-display tracking-widest text-muted hover:text-white transition-all border border-white/5 cursor-pointer"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
