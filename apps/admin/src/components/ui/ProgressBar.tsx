interface ProgressBarProps {
  value: number; // 0-100
  color?: string;
}

export function ProgressBar({ value, color = '#4ADE80' }: ProgressBarProps) {
  return (
    <div className="prog-bar-bg">
      <div className="prog-bar-fill" style={{ width: `${value}%`, backgroundColor: color }} />
    </div>
  );
}
