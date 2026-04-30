
import type { RefObject } from 'react';
import { SEARCH_LABELS } from '@/constants/labels';

interface GreetingHeaderProps {
  greeting: string;
  greetingRef: RefObject<HTMLSpanElement | null>;
  headlineRef: RefObject<HTMLSpanElement | null>;
}

export function GreetingHeader({ greeting, greetingRef, headlineRef }: GreetingHeaderProps) {
  return (
    <h1 className="mx-auto mb-16 flex w-full max-w-3xl flex-col gap-5 text-5xl font-light md:text-7xl">
      <span
        ref={greetingRef}
        className="block self-start text-left font-serif text-4xl italic text-muted md:text-5xl"
      >
        {greeting}
      </span>

      <span
        ref={headlineRef}
        className="hero-gradient-text block self-end text-right font-serif italic"
      >
        {SEARCH_LABELS.headline}
        {SEARCH_LABELS.headlineAccent}
      </span>
    </h1>
  );
}
