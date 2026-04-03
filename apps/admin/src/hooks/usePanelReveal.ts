import { useEffect, useRef } from 'react';
import { panelReveal } from '@/animations/panelReveal';

export function usePanelReveal() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const panels = Array.from(
      containerRef.current.querySelectorAll<HTMLElement>('.glass-panel'),
    );
    if (panels.length > 0) {
      panelReveal(panels);
    }
  }, []);

  return { containerRef };
}
