import { useEffect } from 'react';
import gsap from 'gsap';

export function useMouseAura(containerRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const aura1 = el.querySelector<HTMLElement>('.aura-1');
    const aura2 = el.querySelector<HTMLElement>('.aura-2');
    const aura3 = el.querySelector<HTMLElement>('.aura-3');

    const handleMouseMove = (e: MouseEvent) => {
      if (aura1) gsap.to(aura1, { x: e.clientX * 0.05, y: e.clientY * 0.05, duration: 2, ease: 'power1.out', overwrite: 'auto' });
      if (aura2) gsap.to(aura2, { x: -e.clientX * 0.05, y: -e.clientY * 0.05, duration: 2, ease: 'power1.out', overwrite: 'auto' });
      if (aura3) {
        el.style.setProperty('--aura-x', `${e.clientX}px`);
        el.style.setProperty('--aura-y', `${e.clientY}px`);
      }
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [containerRef]);
}
