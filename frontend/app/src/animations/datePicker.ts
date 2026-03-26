import gsap from 'gsap';

export function animateDatePickerOpen(
  overlay: HTMLElement,
  modal: HTMLElement,
): void {
  gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: 'power2.out' });
  gsap.fromTo(modal, { scale: 0.9, y: 20, opacity: 0 }, { scale: 1, y: 0, opacity: 1, duration: 0.5, ease: 'expo.out' });
}

export function animateDatePickerClose(
  overlay: HTMLElement,
  modal: HTMLElement,
  onComplete: () => void,
): void {
  gsap.to(overlay, { opacity: 0, duration: 0.3, ease: 'power2.in' });
  gsap.to(modal, {
    scale: 0.95, y: 10, opacity: 0, duration: 0.3, ease: 'power2.in',
    onComplete,
  });
}

export function animateDatePickerMonth(
  days: HTMLElement,
  dir: -1 | 1,
  onSwap: () => void,
): void {
  const outX = dir === 1 ? -30 : 30;
  const inX = dir === 1 ? 30 : -30;
  gsap.to(days, {
    opacity: 0, x: outX, duration: 0.2, ease: 'power2.in',
    onComplete: () => {
      onSwap();
      gsap.fromTo(days, { opacity: 0, x: inX }, { opacity: 1, x: 0, duration: 0.3, ease: 'power2.out' });
    },
  });
}
