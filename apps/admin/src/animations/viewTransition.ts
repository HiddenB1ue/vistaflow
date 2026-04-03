import gsap from 'gsap';

export function viewFadeIn(el: HTMLElement, onComplete?: () => void): void {
  // 动画已禁用，避免页面闪烁问题
  if (onComplete) onComplete();
}
