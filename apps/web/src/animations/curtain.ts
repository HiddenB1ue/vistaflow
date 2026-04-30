import gsap from 'gsap';

type CurtainDirection = 'up' | 'down';

/**
 * 剧场级幕布转场动画
 * - 'up'：幕布从下向上覆盖屏幕 + 显示「Flowing...」文字（页面离开前调用）
 * - 'down'：幕布从上向下收起（新页面挂载后调用）
 */
export function createCurtainTimeline(
  el: HTMLElement,
  direction: CurtainDirection,
  onComplete?: () => void,
): gsap.core.Timeline {
  const tl = gsap.timeline({ onComplete });
  const textEl = el.querySelector<HTMLElement>('.loading-text');
  const barContainer = el.querySelector<HTMLElement>('.loading-bar-container');
  const barEl = el.querySelector<HTMLElement>('.loading-bar');

  if (direction === 'up') {
    tl.set(el, { yPercent: 100, display: 'flex' })
      .to(el, { yPercent: 0, duration: 0.55, ease: 'power3.inOut' })
      .to(textEl, { opacity: 1, duration: 0.4, ease: 'power2.out' }, '-=0.1')
      .to(barContainer, { display: 'block', opacity: 1, duration: 0.3 }, '-=0.1')
      .to(barEl, { width: '100%', duration: 0.8, ease: 'power2.inOut' });
  } else {
    tl.to(textEl, { opacity: 0, duration: 0.2, ease: 'power2.in' })
      .to(el, { yPercent: -100, duration: 0.55, ease: 'power3.inOut' }, '-=0.1')
      .set(el, { display: 'none' })
      .set(textEl, { opacity: 0 })
      .set(barEl, { width: '33.333%' });
  }

  return tl;
}
