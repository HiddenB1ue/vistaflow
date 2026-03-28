import { useRef, useEffect } from 'react';
import { createSearchRevealTimeline } from '@/animations/searchReveal';

interface SearchRevealRefs {
  greetingRef: React.RefObject<HTMLElement | null>;
  headlineRef: React.RefObject<HTMLElement | null>;
  formRef: React.RefObject<HTMLElement | null>;
  btnRef: React.RefObject<HTMLElement | null>;
}

export function useSearchReveal(): SearchRevealRefs {
  const greetingRef = useRef<HTMLElement | null>(null);
  const headlineRef = useRef<HTMLElement | null>(null);
  const formRef = useRef<HTMLElement | null>(null);
  const btnRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const greeting = greetingRef.current;
    const headline = headlineRef.current;
    const form = formRef.current;
    const btn = btnRef.current;
    if (!greeting || !headline || !form || !btn) return;

    const tl = createSearchRevealTimeline(greeting, headline, form, btn);
    return () => { tl.kill(); };
  }, []);

  return { greetingRef, headlineRef, formRef, btnRef };
}
