import type React from 'react';

export type BadgeVariant = 'green' | 'yellow' | 'blue' | 'red' | 'purple';

export interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

export function Badge({ variant, children }: BadgeProps) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}
