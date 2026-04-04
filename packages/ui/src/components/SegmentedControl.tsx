import type React from 'react';

export interface SegmentedControlOption<TValue extends string = string> {
  value: TValue;
  label: React.ReactNode;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  disabled?: boolean;
}

export type SegmentedControlSize = 'default' | 'sm';

export interface SegmentedControlProps<TValue extends string = string> {
  value: TValue;
  onChange: (value: TValue) => void;
  options: Array<SegmentedControlOption<TValue>>;
  className?: string;
  size?: SegmentedControlSize;
}

export function SegmentedControl<TValue extends string = string>({
  value,
  onChange,
  options,
  className = '',
  size = 'default',
}: SegmentedControlProps<TValue>) {
  return (
    <div className={`vf-segmented-control vf-segmented-control--${size} ${className}`.trim()} role="tablist">
      {options.map((option) => {
        const active = option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={option.disabled}
            className={`vf-segmented-control__item${active ? ' vf-segmented-control__item--active' : ''}`.trim()}
            onClick={() => onChange(option.value)}
          >
            {option.icon ? <span className="vf-segmented-control__icon">{option.icon}</span> : null}
            <span className="vf-segmented-control__label">{option.label}</span>
            {option.badge ? <span className="vf-segmented-control__badge">{option.badge}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
