import { forwardRef, useEffect, useId, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type React from 'react';

export type ComboboxInputAppearance = 'boxed' | 'hero';

export interface ComboboxInputRef<TOption> {
  getFirstOption: () => TOption | null;
  selectFirstOption: () => boolean;
}

export interface ComboboxInputProps<TOption> {
  value: string;
  onValueChange: (value: string) => void;
  loadOptions: (query: string) => Promise<TOption[]>;
  getOptionId: (option: TOption) => string;
  getOptionLabel: (option: TOption) => string;
  getOptionDescription?: (option: TOption) => React.ReactNode;
  renderOption?: (option: TOption, state: { active: boolean }) => React.ReactNode;
  onSelect?: (option: TOption) => void;
  onEnterKey?: () => void;
  autoSelectOnBlur?: boolean;
  placeholder?: string;
  'aria-label'?: string;
  appearance?: ComboboxInputAppearance;
  emptyText?: React.ReactNode;
  loadingText?: React.ReactNode;
  errorText?: string;
  className?: string;
  menuClassName?: string;
  maxLength?: number;
  debounceMs?: number;
}

function ComboboxInputInner<TOption>(
  {
    value,
    onValueChange,
    loadOptions,
    getOptionId,
    getOptionLabel,
    getOptionDescription,
    renderOption,
    onSelect,
    onEnterKey,
    autoSelectOnBlur = false,
    placeholder,
    'aria-label': ariaLabel,
    appearance = 'boxed',
    emptyText = '\u672a\u627e\u5230\u5339\u914d\u9879',
    loadingText = '\u641c\u7d22\u4e2d\u2026',
    errorText,
    className = '',
    menuClassName = '',
    maxLength = 40,
    debounceMs = 200,
  }: ComboboxInputProps<TOption>,
  ref: React.Ref<ComboboxInputRef<TOption>>
) {
  const menuId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const requestIdRef = useRef(0);
  const hasUserSelectedRef = useRef(false);

  const [options, setOptions] = useState<TOption[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [hasUserSelected, setHasUserSelected] = useState(false);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number; width: number } | null>(null);

  const trimmedValue = value.trim();
  const shouldRenderMenu = open && trimmedValue.length > 0 && (loading || options.length > 0);

  // Update menu position when it opens or on scroll/resize
  useEffect(() => {
    if (!shouldRenderMenu || !inputRef.current) {
      setMenuPosition(null);
      return;
    }

    const updatePosition = () => {
      if (inputRef.current) {
        const rect = inputRef.current.getBoundingClientRect();
        setMenuPosition({
          top: rect.bottom + window.scrollY + 10.4, // 0.65rem = 10.4px
          left: rect.left + window.scrollX,
          width: rect.width,
        });
      }
    };

    updatePosition();

    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [shouldRenderMenu]);

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    getFirstOption: () => (options.length > 0 ? options[0] : null),
    selectFirstOption: () => {
      if (options.length > 0) {
        selectOption(options[0]);
        return true;
      }
      return false;
    },
  }), [options]);

  useEffect(() => {
    if (trimmedValue.length === 0) {
      setOptions([]);
      setOpen(false);
      setActiveIndex(-1);
      setLoading(false);
      return;
    }

    // Don't trigger search if user just selected an option
    if (hasUserSelectedRef.current) {
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
    setHasUserSelected(true);
    hasUserSelectedRef.current = true;
  };

  const handleBlur = () => {
    // Use setTimeout to allow click events on options to fire first
    setTimeout(() => {
      // Auto-select first option on blur if enabled and user hasn't manually selected
      if (autoSelectOnBlur && !hasUserSelectedRef.current && options.length > 0 && trimmedValue.length > 0) {
        selectOption(options[0]);
      }
      // Always close the menu on blur
      setOpen(false);
    }, 200);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      // Enter key: auto-select first option if available, then trigger onEnterKey
      if (options.length > 0 && activeIndex >= 0) {
        event.preventDefault();
        const option = options[activeIndex];
        if (option) {
          selectOption(option);
          // Call onEnterKey after selection to move to next field
          setTimeout(() => onEnterKey?.(), 0);
        }
        return;
      }
      
      // If no options but onEnterKey is provided, just trigger it
      if (onEnterKey) {
        event.preventDefault();
        onEnterKey();
        return;
      }
    }

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

    if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} className={`vf-combobox vf-combobox--${appearance}`.trim()}>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(event) => {
          onValueChange(event.target.value);
          setHasUserSelected(false);
          hasUserSelectedRef.current = false;
        }}
        onFocus={async () => {
          if (trimmedValue.length > 0) {
            // If there are no options, trigger a search
            if (options.length === 0) {
              setLoading(true);
              try {
                const nextOptions = await loadOptions(trimmedValue);
                setOptions(nextOptions);
                setActiveIndex(nextOptions.length > 0 ? 0 : -1);
              } catch {
                setOptions([]);
                setActiveIndex(-1);
              } finally {
                setLoading(false);
              }
            }
            setOpen(true);
          }
        }}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-controls={menuId}
        aria-expanded={shouldRenderMenu}
        maxLength={maxLength}
        className={resolvedInputClassName}
      />

      {/* Error text */}
      {errorText && (
        <div className="vf-combobox__error" style={{ 
          marginTop: '0.5rem', 
          fontSize: '0.875rem', 
          color: '#EF4444' 
        }}>
          {errorText}
        </div>
      )}

      {shouldRenderMenu && menuPosition && createPortal(
        <div 
          id={menuId} 
          role="listbox" 
          className={`vf-combobox__menu ${menuClassName}`.trim()}
          style={{
            position: 'fixed',
            top: `${menuPosition.top}px`,
            left: `${menuPosition.left}px`,
            minWidth: `${menuPosition.width}px`,
          }}
        >
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
        </div>,
        document.body
      )}
    </div>
  );
}

export const ComboboxInput = forwardRef(ComboboxInputInner) as <TOption>(
  props: ComboboxInputProps<TOption> & { ref?: React.Ref<ComboboxInputRef<TOption>> }
) => ReturnType<typeof ComboboxInputInner>;
