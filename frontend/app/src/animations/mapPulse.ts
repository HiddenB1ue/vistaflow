import gsap from 'gsap';

/**
 * 地图脉冲点动画
 * @param el - 脉冲圆圈 SVG 元素
 */
export function createMapPulseTimeline(el: SVGCircleElement): gsap.core.Timeline {
  const tl = gsap.timeline({ repeat: -1 });
  tl.fromTo(
    el,
    { scale: 1, opacity: 0.8, transformOrigin: '50% 50%' },
    { scale: 2.5, opacity: 0, duration: 1.5, ease: 'power1.out' },
  );
  return tl;
}
