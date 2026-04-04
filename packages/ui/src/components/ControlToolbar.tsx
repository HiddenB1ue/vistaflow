import type React from 'react';
import { PanelCard } from './PanelCard';

export interface ControlToolbarProps {
  children: React.ReactNode;
  className?: string;
}

export interface ControlToolbarSectionProps {
  children: React.ReactNode;
  className?: string;
}

export function ControlToolbar({ children, className = '' }: ControlToolbarProps) {
  return <PanelCard className={`vf-control-toolbar ${className}`.trim()}>{children}</PanelCard>;
}

export function ControlToolbarMain({ children, className = '' }: ControlToolbarSectionProps) {
  return <div className={`vf-control-toolbar__main ${className}`.trim()}>{children}</div>;
}

export function ControlToolbarActions({ children, className = '' }: ControlToolbarSectionProps) {
  return <div className={`vf-control-toolbar__actions ${className}`.trim()}>{children}</div>;
}
