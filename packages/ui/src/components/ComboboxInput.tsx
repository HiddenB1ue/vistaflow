import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type React from 'react';

export type ComboboxInputAppearance = 'boxed' | 'hero';

export interface ComboboxInputProps<TOption> {
  value: string;
  onValueChange: (value: string) => void;
  loadOptions: (query: string) => Promise<TOption[]>;
  getOptionId: (option: TOption) => string;
  getOptionLabel: (option: TOption) => string;
  getOptionDescription?: (option: TOption) => React.ReactNode;
  renderOption?: (option: TOption, state: { active: boolean }) => React.ReactNode;
  onSelect?: (option: TOption) => void;
  placeholder?: string;
  'aria-label'?: string;
  appearance?: ComboboxInputAppearance;
  emptyText?: React.ReactNode;
  loadingText?: React.ReactNode;
  className?: string;
  menuClassName?: string;
  maxLength?: number;
  debounceMs?: number;
}

export function ComboboxInput<TOption>({
  value,
  onValueChange,
  loadOptions,
  getOptionId,
  getOptionLabel,
  getOptionDescription,
  renderOption,
  onSelect,
  placeholder,
  'aria-label': ariaLabel,
  appearance = 'boxed',
  emptyText = '\u672a\u627e\u5230\u5339\u914d\u9879',
  loadingText = '\u641c\u7d22\u4e2d\u2026',
  className = '',
  menuClassName = '',
  maxLength = 40,
  debounceMs = 200,
}: ComboboxInputProps<TOption>) {
  const menuId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const requestIdRef = useRef(0);

  const [options, setOptions] = useState<TOption[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const trimmedValue = value.trim();
  const shouldRenderMenu = open && trimmedValue.length > 0 && (loading || options.length > 0);

  useEffect(() => {
    if (trimmedValue.length === 0) {
      setOptions([]);
      setOpen(false);
      setActiveIndex(-1);
      setLoading(false);
      return;
    }

    const currentRequestId = ++requestIdRef.current;
    const timer = window.setTimeout(async () => {
      setLoading(true);

      try {
        const nextOptions = await loadOptions(trimmedValue);
        if (requestIdRef.current !== currentRequestId) return;

        setOptions(nextOptions);
        setOpen(true);
        setActiveIndex(nextOptions.length > 0 ? 0 : -1);
      } catch {
        if (requestIdRef.current !== currentRequestId) return;
        setOptions([]);
        setOpen(true);
        setActiveIndex(-1);
      } finally {
        if (requestIdRef.current === currentRequestId) {
          setLoading(false);
        }
      }
    }, debounceMs);

    return () => window.clearTimeout(timer);
  }, [debounceMs, loadOptions, trimmedValue]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const resolvedInputClassName = useMemo(() => {
    const base = appearance === 'hero'
      ? 'vf-combobox__input vf-combobox__input--hero'
      : 'vf-combobox__input vf-combobox__input--boxed input-box';

    return `${base} ${className}`.trim();
  }, [appearance, className]);

  const selectOption = (option: TOption) => {
    const nextValue = getOptionLabel(option);
    onValueChange(nextValue);
    onSelect?.(option);
    setOpen(false);
    setOptions([]);
    setActiveIndex(-1);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!shouldRenderMenu) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((current) => Math.min(current + 1, options.length - 1));
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((current) => Math.max(current - 1, 0));
      return;
    }

    if (event.key === 'Enter' && activeIndex >= 0 && activeIndex < options.length) {
      event.preventDefault();
      const option = options[activeIndex];
      if (option) {
        selectOption(option);
      }
      return;
    }

    if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} className={`vf-combobox vf-combobox--${appearance}`.trim()}>
      <input
        type="text"
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        onFocus={() => {
          if (trimmedValue.length > 0) {
            setOpen(true);
          }
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-controls={menuId}
        aria-expanded={shouldRenderMenu}
        maxLength={maxLength}
        className={resolvedInputClassName}
      />

      {shouldRenderMenu ? (
        <div id={menuId} role="listbox" className={`vf-combobox__menu ${menuClassName}`.trim()}>
          {loading ? <div className="vf-combobox__empty">{loadingText}</div> : null}

          {!loading && options.map((option, index) => {
            const active = index === activeIndex;

            return (
              <button
                key={getOptionId(option)}
                type="button"
                role="option"
                aria-selected={active}
                className={`vf-combobox__option${active ? ' vf-combobox__option--active' : ''}`.trim()}
                onMouseDown={() => selectOption(option)}
                onMouseEnter={() => setActiveIndex(index)}
              >
                {renderOption
                  ? renderOption(option, { active })
                  : (
                    <>
                      <span className="vf-combobox__option-label">{getOptionLabel(option)}</span>
                      {getOptionDescription ? (
                        <span className="vf-combobox__option-description">{getOptionDescription(option)}</span>
                      ) : null}
                    </>
                  )}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
