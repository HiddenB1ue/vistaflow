import { useRef, useEffect, useCallback } from 'react';
import { createCardRevealTimeline } from '@/animations/cardReveal';

export function useCardReveal(deps: unknown[]) {
  const listRef = useRef<HTMLDivElement>(null);

  const triggerReveal = useCallback(() => {
    const els = Array.from(
      listRef.current?.querySelectorAll<HTMLElement>('[data-card]') ?? [],
    );
    if (els.length > 0) createCardRevealTimeline(els);
  }, []);

  useEffect(() => {
    // 等下一帧确保 DOM 已渲染
    const raf = requestAnimationFrame(triggerReveal);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return listRef;
}
