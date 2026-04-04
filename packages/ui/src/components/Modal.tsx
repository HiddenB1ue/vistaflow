
import type React from 'react';
import { createPortal } from 'react-dom';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl';
export type ModalFooterAlign = 'start' | 'end' | 'between';

export interface ModalShellProps {
  open: boolean;
  children: React.ReactNode;
  className?: string;
  overlayClassName?: string;
  size?: ModalSize;
  onBackdropClick?: () => void;
}

export interface ModalHeaderProps {
  title: React.ReactNode;
  eyebrow?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  onClose?: () => void;
  closeLabel?: string;
  className?: string;
}

export interface ModalSectionProps {
  children: React.ReactNode;
  className?: string;
}

export interface ModalFooterProps extends ModalSectionProps {
  align?: ModalFooterAlign;
}

export function ModalShell({
  open,
  children,
  className = '',
  overlayClassName = '',
  size = 'lg',
  onBackdropClick,
}: ModalShellProps) {
  const content = (
    <div
      className={`vf-modal-overlay${open ? ' vf-modal-overlay--open' : ''} ${overlayClassName}`.trim()}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onBackdropClick?.();
        }
      }}
      aria-hidden={!open}
    >
      <div
        role="dialog"
        aria-modal="true"
        className={`vf-modal-shell vf-modal-shell--${size} ${className}`.trim()}
        onMouseDown={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );

  if (typeof document === 'undefined') {
    return content;
  }

  return createPortal(content, document.body);
}

export function ModalHeader({
  title,
  eyebrow,
  subtitle,
  actions,
  onClose,
  closeLabel = 'Close',
  className = '',
}: ModalHeaderProps) {
  return (
    <header className={`vf-modal-header ${className}`.trim()}>
      <div className="vf-modal-header__lead">
        {eyebrow ? <div className="vf-modal-header__eyebrow">{eyebrow}</div> : null}
        <div className="vf-modal-header__title">{title}</div>
        {subtitle ? <div className="vf-modal-header__subtitle">{subtitle}</div> : null}
      </div>

      {(actions || onClose) ? (
        <div className="vf-modal-header__actions">
          {actions}
          {onClose ? (
            <button
              type="button"
              aria-label={closeLabel}
              className="vf-modal-header__close"
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

export function ModalBody({ children, className = '' }: ModalSectionProps) {
  return <div className={`vf-modal-body ${className}`.trim()}>{children}</div>;
}

export function ModalFooter({ children, align = 'end', className = '' }: ModalFooterProps) {
  return (
    <footer className={`vf-modal-footer vf-modal-footer--align-${align} ${className}`.trim()}>
      {children}
    </footer>
  );
}
