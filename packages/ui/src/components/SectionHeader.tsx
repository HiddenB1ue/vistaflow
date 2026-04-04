import type React from 'react';

export interface SectionHeaderProps {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  eyebrow?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  actions,
  eyebrow,
  className = '',
}: SectionHeaderProps) {
  return (
    <div className={`vf-section-header ${className}`.trim()}>
      <div className="vf-section-header__lead">
        {eyebrow ? <div className="vf-section-header__eyebrow">{eyebrow}</div> : null}
        <div className="vf-section-header__title">{title}</div>
        {subtitle ? <div className="vf-section-header__subtitle">{subtitle}</div> : null}
      </div>
      {actions ? <div className="vf-section-header__actions">{actions}</div> : null}
    </div>
  );
}
