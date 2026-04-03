import { useCallback, useRef } from 'react';
import { viewFadeIn } from '@/animations/viewTransition';

export function useViewTransition() {
  const containerRef = useRef<HTMLDivElement>(null);

  const animateIn = useCallback(() => {
    if (containerRef.current) {
      viewFadeIn(containerRef.current);
    }
  }, []);

  return { containerRef, animateIn };
}
