import type React from 'react';

export type ContentSectionSpacing = 'default' | 'dense' | 'hero';
export type ContentSectionWidth = 'full' | 'default' | 'wide';

export interface ContentSectionProps {
  children: React.ReactNode;
  className?: string;
  as?: 'div' | 'section' | 'main';
  spacing?: ContentSectionSpacing;
  width?: ContentSectionWidth;
}

export function ContentSection({
  children,
  className = '',
  as = 'section',
  spacing = 'default',
  width = 'full',
}: ContentSectionProps) {
  const Comp = as;

  return (
    <Comp
      className={`vf-content-section vf-content-section--${spacing} vf-content-section--width-${width} ${className}`.trim()}
    >
      {children}
    </Comp>
  );
}
