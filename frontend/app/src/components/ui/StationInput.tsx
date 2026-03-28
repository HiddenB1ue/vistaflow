import { useEffect, useRef, useState } from 'react';
import type { SearchSuggestion } from '@/types/search';
import { fetchStationSuggestions } from '@/services/stationService';

interface StationInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  'aria-label'?: string;
}

function useDebounce(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export function StationInput({
  value,
  onChange,
  placeholder,
  'aria-label': ariaLabel,
}: StationInputProps) {
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const debouncedValue = useDebounce(value, 200);

  // Fetch suggestions when debounced value changes
  useEffect(() => {
    if (debouncedValue.trim().length === 0) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    let cancelled = false;
    fetchStationSuggestions(debouncedValue).then((items) => {
      if (!cancelled) {
        setSuggestions(items);
        setOpen(items.length > 0);
        setActiveIndex(-1);
      }
    }).catch(() => {
      if (!cancelled) setSuggestions([]);
    });
    return () => { cancelled = true; };
  }, [debouncedValue]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function selectSuggestion(item: SearchSuggestion) {
    onChange(item.name);
    setSuggestions([]);
    setOpen(false);
    setActiveIndex(-1);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[activeIndex]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <div ref={containerRef} className="relative inline-block">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-expanded={open}
        maxLength={20}
        className="nl-input mx-4"
      />

      {open && (
        <ul
          role="listbox"
          className="absolute left-4 top-full mt-2 min-w-[160px] rounded-xl overflow-hidden z-50"
          style={{
            background: 'rgba(10, 10, 16, 0.92)',
            border: '1px solid rgba(255,255,255,0.08)',
            backdropFilter: 'blur(16px)',
          }}
        >
          {suggestions.map((item, idx) => (
            <li
              key={item.id}
              role="option"
              aria-selected={idx === activeIndex}
              onMouseDown={() => selectSuggestion(item)}
              onMouseEnter={() => setActiveIndex(idx)}
              className="px-4 py-3 cursor-pointer text-sm transition-colors"
              style={{
                color: idx === activeIndex ? 'var(--color-pulse)' : 'rgba(255,255,255,0.75)',
                background: idx === activeIndex ? 'rgba(255,255,255,0.06)' : 'transparent',
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: '1rem',
              }}
            >
              {item.name}
              {item.code && (
                <span
                  className="ml-2 text-xs"
                  style={{ color: 'rgba(255,255,255,0.3)' }}
                >
                  {item.code}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
