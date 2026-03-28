import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { createCurtainTimeline } from '@/animations/curtain';
import { useUiStore } from '@/stores/uiStore';

export function usePageTransition() {
  const navigate = useNavigate();
  const curtainEl = useUiStore((s) => s.curtainEl);
  const setCurtainEl = useUiStore((s) => s.setCurtainEl);
  const setTransitioning = useUiStore((s) => s.setTransitioning);

  const setCurtainRef = useCallback(
    (el: HTMLElement | null) => setCurtainEl(el),
    [setCurtainEl],
  );

  const navigateTo = useCallback(
    (to: string) => {
      // 实时读取，避免闭包捕获旧的 null 值
      const target = curtainEl ?? document.querySelector<HTMLElement>('.transition-overlay');
      if (!target) {
        navigate(to);
        return;
      }
      setTransitioning(true);
      createCurtainTimeline(target, 'up', () => {
        navigate(to);
      });
    },
    [curtainEl, navigate, setTransitioning],
  );

  // el 参数：直接传入避免 Store 竞态；不传则从 Store 读取
  const revealPage = useCallback(
    (el?: HTMLElement | null) => {
      const run = (target: HTMLElement) => {
        createCurtainTimeline(target, 'down', () => {
          setTransitioning(false);
        });
      };

      if (el) {
        run(el);
        return;
      }

      if (curtainEl) {
        run(curtainEl);
        return;
      }

      // 兜底：Store 可能还未同步，用 rAF 重试一次
      const raf = requestAnimationFrame(() => {
        const fallback = document.querySelector<HTMLElement>('.transition-overlay');
        if (fallback) run(fallback);
      });
      return () => cancelAnimationFrame(raf);
    },
    [curtainEl, setTransitioning],
  );

  return { setCurtainRef, navigateTo, revealPage };
}
