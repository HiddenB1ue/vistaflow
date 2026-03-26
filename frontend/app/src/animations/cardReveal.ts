import gsap from 'gsap';

/**
 * 方案卡片入场动画
 * @param els - 卡片 DOM 元素数组
 */
export function createCardRevealTimeline(els: HTMLElement[]): gsap.core.Timeline {
  const tl = gsap.timeline();
  tl.fromTo(
    els,
    { opacity: 0, y: 24 },
    { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out' },
  );
  return tl;
}
