import { NumberWheel } from '@vistaflow/ui';

interface TimeWheelFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function parseTime(value: string): { hour: number; minute: number } {
  const [rawHour, rawMinute] = value.split(':', 2);
  const hour = Number.parseInt(rawHour ?? '', 10);
  const minute = Number.parseInt(rawMinute ?? '', 10);

  return {
    hour: Number.isInteger(hour) ? Math.min(Math.max(hour, 0), 23) : 0,
    minute: Number.isInteger(minute) ? Math.min(Math.max(minute, 0), 59) : 0,
  };
}

function buildTime(hour: number, minute: number): string {
  return `${pad(hour)}:${pad(minute)}`;
}

export function TimeWheelField({ label, value, onChange }: TimeWheelFieldProps) {
  const { hour, minute } = parseTime(value);

  return (
    <div className="space-y-2">
      <label className="vf-drawer-label">{label}</label>

      <div className="flex items-center gap-2">
        <div className="grid flex-1 grid-cols-2 gap-2">
          <NumberWheel
            value={hour}
            min={0}
            max={23}
            onChange={(nextHour) => onChange(buildTime(nextHour, minute))}
            label="时"
          />
          <NumberWheel
            value={minute}
            min={0}
            max={59}
            onChange={(nextMinute) => onChange(buildTime(hour, nextMinute))}
            label="分"
          />
        </div>

        <button
          type="button"
          className="h-11 rounded-full border border-white/10 px-3 text-xs tracking-[0.16em] text-muted transition hover:border-white/25 hover:text-white"
          onClick={() => onChange('')}
        >
          不限
        </button>
      </div>
    </div>
  );
}
