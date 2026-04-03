import { useState, useRef, useEffect } from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface CustomSelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function CustomSelect({ options, value, onChange, className = '' }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const selectedLabel = options.find(o => o.value === value)?.label ?? '';

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isOpen]);

  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false);
    }
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  return (
    <div className={`custom-select-wrapper ${className}`} ref={wrapperRef}>
      <div className={`custom-select-trigger ${isOpen ? 'open' : ''}`} onClick={() => setIsOpen(!isOpen)} tabIndex={0}>
        <span className="select-label">{selectedLabel}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      <div className={`custom-select-dropdown ${isOpen ? 'open' : ''}`}>
        {options.map((opt) => (
          <div key={opt.value} className={`custom-select-option ${opt.value === value ? 'selected' : ''}`} onClick={() => { onChange(opt.value); setIsOpen(false); }}>
            {opt.label}
          </div>
        ))}
      </div>
    </div>
  );
}
