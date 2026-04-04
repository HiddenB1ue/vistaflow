import type React from 'react';

export type ButtonVariant = 'primary' | 'outline' | 'danger' | 'warning' | 'success';
export type ButtonSize = 'default' | 'sm';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

export function Button({
  variant = 'outline',
  size = 'default',
  type = 'button',
  children,
  className = '',
  ...rest
}: ButtonProps) {
  const cls = `btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''} ${className}`;
  return <button type={type} className={cls} {...rest}>{children}</button>;
}
