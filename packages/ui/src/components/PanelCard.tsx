import type React from 'react';
import { GlassPanel } from './GlassPanel';

export interface PanelCardProps {
  children: React.ReactNode;
  className?: string;
}

export interface PanelSectionProps {
  children: React.ReactNode;
  className?: string;
}

export function PanelCard({ children, className = '' }: PanelCardProps) {
  return <GlassPanel className={`vf-panel-card ${className}`.trim()}>{children}</GlassPanel>;
}

export function PanelBody({ children, className = '' }: PanelSectionProps) {
  return <div className={`vf-panel-body ${className}`.trim()}>{children}</div>;
}
