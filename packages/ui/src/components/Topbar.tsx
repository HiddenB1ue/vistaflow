import type React from 'react';

export type TopbarBlendMode = 'default' | 'difference';

export interface TopbarProps {
  children: React.ReactNode;
  className?: string;
  fixed?: boolean;
  blendMode?: TopbarBlendMode;
}

export interface TopbarBrandProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

export interface TopbarActionsProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Topbar({
  children,
  className = '',
  fixed = true,
  blendMode = 'default',
}: TopbarProps) {
  return (
    <header className={`vf-topbar${fixed ? ' vf-topbar--fixed' : ''} vf-topbar--blend-${blendMode} ${className}`.trim()}>
      <div className="vf-topbar-shell">{children}</div>
    </header>
  );
}

export function TopbarBrand({ children, className = '', type = 'button', ...rest }: TopbarBrandProps) {
  return (
    <button type={type} className={`vf-topbar__brand ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}

export function TopbarActions({ children, className = '', ...rest }: TopbarActionsProps) {
  return (
    <div className={`vf-topbar__actions ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}
