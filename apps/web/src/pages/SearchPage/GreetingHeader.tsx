
import type { RefObject } from 'react';

interface GreetingHeaderProps {
  logoRef: RefObject<HTMLSpanElement | null>;
  brandRef: RefObject<HTMLSpanElement | null>;
}

export function GreetingHeader({ logoRef, brandRef }: GreetingHeaderProps) {
  return (
    <h1
      className="mx-auto mb-16 flex w-full items-center justify-center gap-4 text-5xl font-light md:gap-6 md:text-7xl"
      aria-label="VistaFlow"
    >
      <span
        ref={logoRef}
        className="flex h-16 w-16 shrink-0 items-center justify-center md:h-20 md:w-20"
        aria-hidden="true"
      >
        <img
          src="/vistaflow-brand-mark.svg"
          alt=""
          className="h-full w-full object-contain"
        />
      </span>

      <span
        ref={brandRef}
        className="hero-gradient-text block font-serif italic"
        aria-hidden="true"
      >
        VistaFlow
      </span>
    </h1>
  );
}
