export interface NumberWheelProps {
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  step?: number;
  padLength?: number;
  label?: string;
  className?: string;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function formatValue(value: number, padLength: number): string {
  return String(value).padStart(padLength, '0');
}

export function getNumberWheelValue(
  value: number,
  direction: -1 | 1,
  options: { min: number; max: number; step?: number; wrap?: boolean },
): number {
  const { min, max, step = 1, wrap = true } = options;
  const next = value + direction * step;
  if (next > max) {
    return wrap ? min : max;
  }
  if (next < min) {
    return wrap ? max : min;
  }
  return clamp(next, min, max);
}

export function getNumberWheelItems(
  value: number,
  options: { min: number; max: number; step?: number; wrap?: boolean },
): [number, number, number] {
  const { min, max, step = 1, wrap = true } = options;
  const current = clamp(value, min, max);
  return [
    getNumberWheelValue(current, -1, { min, max, step, wrap }),
    current,
    getNumberWheelValue(current, 1, { min, max, step, wrap }),
  ];
}

export function getNumberWheelDirection(deltaY: number): -1 | 1 | 0 {
  if (deltaY > 0) {
    return 1;
  }
  if (deltaY < 0) {
    return -1;
  }
  return 0;
}

export function normalizeNumberWheelInput(
  input: string,
  options: { min: number; max: number; step?: number },
): number | null {
  const { min, max, step = 1 } = options;
  if (!/^\d+$/.test(input)) {
    return null;
  }
  const parsed = Number.parseInt(input, 10);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    return null;
  }
  const offset = parsed - min;
  if (offset % step !== 0) {
    return null;
  }
  return parsed;
}

export function appendNumberWheelInput(
  currentInput: string,
  key: string,
  options: { padLength: number },
): string {
  const { padLength } = options;
  if (!/^\d$/.test(key)) {
    return currentInput;
  }
  return `${currentInput}${key}`.slice(-padLength);
}

export function NumberWheel({
  value,
  min,
  max,
  onChange,
  step = 1,
  padLength = 2,
  label,
  className = '',
}: NumberWheelProps) {
  const current = clamp(value, min, max);

  return (
    <label className={`vf-number-wheel ${className}`.trim()}>
      <input
        className="vf-number-wheel__input"
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        step={step}
        value={formatValue(current, padLength)}
        aria-label={label}
        onChange={(event) => {
          const normalized = normalizeNumberWheelInput(event.target.value, { min, max, step });
          if (normalized !== null) {
            onChange(normalized);
          }
        }}
      />
      {label ? <span className="vf-number-wheel__label">{label}</span> : null}
    </label>
  );
}
