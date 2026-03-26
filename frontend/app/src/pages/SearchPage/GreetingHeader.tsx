import { useTimeGreeting } from '@/hooks/useTimeGreeting';

interface GreetingHeaderProps {
  greetingRef: React.RefObject<HTMLElement | null>;
  headlineRef: React.RefObject<HTMLElement | null>;
}

export function GreetingHeader({ greetingRef, headlineRef }: GreetingHeaderProps) {
  const greeting = useTimeGreeting();

  return (
    <h1
      className="text-5xl md:text-7xl font-light tracking-widest mb-16"
      style={{ color: 'var(--color-text-primary)' }}
    >
      <span
        ref={greetingRef as React.RefObject<HTMLSpanElement>}
        className="font-serif italic text-4xl block mb-6"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {greeting}，旅行者。
      </span>
      <span ref={headlineRef as React.RefObject<HTMLSpanElement>}>
        智能规划，
        <span className="font-serif italic" style={{ color: 'var(--color-pulse)' }}>
          让出行更简单。
        </span>
      </span>
    </h1>
  );
}
