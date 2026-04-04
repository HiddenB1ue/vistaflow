import type React from 'react';

export type PageHeaderAlign = 'left' | 'center';

export interface PageHeaderProps {
  title: React.ReactNode;
  eyebrow?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  align?: PageHeaderAlign;
  sticky?: boolean;
  className?: string;
}

export function PageHeader({
  title,
  eyebrow,
  subtitle,
  actions,
  align = 'left',
  sticky = false,
  className = '',
}: PageHeaderProps) {
  return (
    <header
      className={`vf-page-header vf-page-header--${align}${sticky ? ' vf-page-header--sticky' : ''} ${className}`.trim()}
    >
      <div className="vf-page-header__lead">
        {eyebrow ? <div className="vf-page-header__eyebrow">{eyebrow}</div> : null}
        <h1 className="vf-page-header__title">{title}</h1>
        {subtitle ? <div className="vf-page-header__subtitle">{subtitle}</div> : null}
      </div>
      {actions ? <div className="vf-page-header__actions">{actions}</div> : null}
    </header>
  );
}
