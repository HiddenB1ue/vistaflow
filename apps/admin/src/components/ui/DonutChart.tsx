interface DonutChartProps {
  percentage: number;
  label: string;
  sublabel?: string;
}

export function DonutChart({ percentage, label, sublabel }: DonutChartProps) {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percentage / 100);

  return (
    <svg viewBox="0 0 120 120" className="w-32 h-32">
      <circle cx="60" cy="60" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
      <circle
        cx="60" cy="60" r={radius} fill="none"
        stroke="#8B5CF6" strokeWidth={10}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 60 60)"
        style={{ filter: 'drop-shadow(0 0 6px rgba(139,92,246,0.5))' }}
      />
      <text x="60" y="55" textAnchor="middle" fontFamily="Space Grotesk" fontSize={18} fill="#F5F5F7" fontWeight={500}>
        {label}
      </text>
      {sublabel && (
        <text x="60" y="70" textAnchor="middle" fontFamily="Inter" fontSize={8} fill="rgba(138,138,142,0.8)">
          {sublabel}
        </text>
      )}
    </svg>
  );
}
