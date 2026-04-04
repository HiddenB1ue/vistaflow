
import type { RefObject } from 'react';
import { SEARCH_LABELS } from '@/constants/labels';

interface GreetingHeaderProps {
  greeting: string;
  greetingRef: RefObject<HTMLSpanElement | null>;
  headlineRef: RefObject<HTMLSpanElement | null>;
}

export function GreetingHeader({ greeting, greetingRef, headlineRef }: GreetingHeaderProps) {
  return (
    <h1 className="mb-16 text-5xl font-light tracking-widest md:text-7xl">
      <span ref={greetingRef} className="mb-6 block font-serif text-4xl italic text-muted">
        {greeting}
      </span>
      {SEARCH_LABELS.headline}
      <span ref={headlineRef} className="font-serif italic time-theme-text">
        {SEARCH_LABELS.headlineAccent}
      </span>
    </h1>
  );
}
