import type { ReactNode } from 'react';

interface KpiCardProps {
  label: string;
  value: string | number | ReactNode;
  accentColor?: string;
  trend?: ReactNode;
  subtitle?: ReactNode;
  alertDot?: boolean;
  valueClassName?: string;
}

export function KpiCard({ label, value, accentColor, trend, subtitle, alertDot, valueClassName = '' }: KpiCardProps) {
  const borderStyle = accentColor ? { borderLeft: `3px solid ${accentColor}` } : {};
  return (
    <div className="glass-panel p-5" style={borderStyle}>
      <div className="flex items-center gap-2 mb-1">
        <div className="text-[10px] text-[#8A8A8E] tracking-widest uppercase">{label}</div>
        {alertDot && <span className="w-2 h-2 rounded-full bg-[#FACC15] animate-ping" />}
      </div>
      <div className={`text-3xl font-display font-light count-up ${valueClassName}`}>{value}</div>
      {trend && <div className="text-xs text-[#4ADE80] mt-2 flex items-center gap-1">{trend}</div>}
      {subtitle && <div className="text-xs text-[#8A8A8E] mt-2">{subtitle}</div>}
    </div>
  );
}
