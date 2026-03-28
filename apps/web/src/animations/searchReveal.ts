import gsap from 'gsap';

/**
 * SearchPage 内容入场动画
 * @param greetingEl - 问候语元素
 * @param headlineEl - 主标题元素
 * @param formEl - 搜索表单元素
 * @param btnEl - 搜索按钮元素
 */
export function createSearchRevealTimeline(
  greetingEl: HTMLElement,
  headlineEl: HTMLElement,
  formEl: HTMLElement,
  btnEl: HTMLElement,
): gsap.core.Timeline {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  tl.fromTo(greetingEl, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.8 })
    .fromTo(headlineEl, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.8 }, '-=0.5')
    .fromTo(formEl, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.7 }, '-=0.5')
    .fromTo(btnEl, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.6 }, '-=0.4');
  return tl;
}
