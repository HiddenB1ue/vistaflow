
import type React from 'react';

export interface DrawerShellProps {
  open: boolean;
  children: React.ReactNode;
  className?: string;
}

export interface DrawerHeaderProps {
  title: React.ReactNode;
  eyebrow?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  onClose?: () => void;
  closeLabel?: string;
  className?: string;
}

export interface DrawerSectionProps {
  children: React.ReactNode;
  className?: string;
}

export interface DrawerBodyProps extends DrawerSectionProps {}

export type DrawerFooterAlign = 'start' | 'end' | 'between';

export interface DrawerFooterProps extends DrawerSectionProps {
  align?: DrawerFooterAlign;
}

export function DrawerShell({ open, children, className = '' }: DrawerShellProps) {
  return (
    <aside className={`vf-drawer-shell${open ? ' vf-drawer-shell--open' : ''} ${className}`.trim()}>
      {children}
    </aside>
  );
}

export function DrawerHeader({
  title,
  eyebrow,
  subtitle,
  actions,
  onClose,
  closeLabel = 'Close',
  className = '',
}: DrawerHeaderProps) {
  return (
    <header className={`vf-drawer-header ${className}`.trim()}>
      <div className="vf-drawer-header__lead">
        {eyebrow ? <div className="vf-drawer-header__eyebrow">{eyebrow}</div> : null}
        <div className="vf-drawer-header__title">{title}</div>
        {subtitle ? <div className="vf-drawer-header__subtitle">{subtitle}</div> : null}
      </div>

      {(actions || onClose) ? (
        <div className="vf-drawer-header__actions">
          {actions}
          {onClose ? (
            <button
              type="button"
              aria-label={closeLabel}
              className="vf-drawer-header__close"
              onClick={onClose}
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          ) : null}
        </div>
      ) : null}
    </header>
  );
}

export function DrawerBody({ children, className = '' }: DrawerBodyProps) {
  return <div className={`vf-drawer-body ${className}`.trim()}>{children}</div>;
}

export function DrawerFooter({ children, align = 'end', className = '' }: DrawerFooterProps) {
  return (
    <footer className={`vf-drawer-footer vf-drawer-footer--align-${align} ${className}`.trim()}>
      {children}
    </footer>
  );
}
