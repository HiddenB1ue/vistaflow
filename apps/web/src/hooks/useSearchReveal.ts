import { useRef, useEffect } from 'react';
import { createSearchRevealTimeline } from '@/animations/searchReveal';

interface SearchRevealRefs {
  logoRef: React.RefObject<HTMLElement | null>;
  brandRef: React.RefObject<HTMLElement | null>;
  formRef: React.RefObject<HTMLElement | null>;
  btnRef: React.RefObject<HTMLElement | null>;
}

export function useSearchReveal(): SearchRevealRefs {
  const logoRef = useRef<HTMLElement | null>(null);
  const brandRef = useRef<HTMLElement | null>(null);
  const formRef = useRef<HTMLElement | null>(null);
  const btnRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const logo = logoRef.current;
    const brand = brandRef.current;
    const form = formRef.current;
    const btn = btnRef.current;
    if (!logo || !brand || !form || !btn) return;

    const tl = createSearchRevealTimeline(logo, brand, form, btn);
    return () => { tl.kill(); };
  }, []);

  return { logoRef, brandRef, formRef, btnRef };
}
