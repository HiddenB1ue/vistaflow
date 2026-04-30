import gsap from 'gsap';

/**
 * SearchPage content reveal animation.
 */
export function createSearchRevealTimeline(
  logoEl: HTMLElement,
  brandEl: HTMLElement,
  formEl: HTMLElement,
  btnEl: HTMLElement,
): gsap.core.Timeline {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  tl.fromTo(logoEl, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.8 })
    .fromTo(brandEl, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.8 }, '-=0.5')
    .fromTo(formEl, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.7 }, '-=0.5')
    .fromTo(btnEl, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.6 }, '-=0.4');
  return tl;
}
