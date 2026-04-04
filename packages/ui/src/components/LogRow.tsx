import type React from 'react';

export interface LogRowProps {
  timestamp: React.ReactNode;
  badge?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function LogRow({ timestamp, badge, children, className = '' }: LogRowProps) {
  return (
    <div className={`vf-log-row ${className}`.trim()}>
      <span className="vf-log-row__time">{timestamp}</span>
      {badge ? <span className="vf-log-row__badge">{badge}</span> : null}
      <span className="vf-log-row__content">{children}</span>
    </div>
  );
}
