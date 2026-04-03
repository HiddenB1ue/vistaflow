import { useRef } from 'react';
import { useMouseAura } from '@vistaflow/utils';

export interface AuraBackgroundProps {
  enableMouseTracking?: boolean;
}

export function AuraBackground({ enableMouseTracking = false }: AuraBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  if (enableMouseTracking) {
    return <AuraBackgroundWithTracking containerRef={containerRef} />;
  }

  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <div
        className="absolute rounded-full"
        style={{
          width: '60vw',
          height: '60vw',
          top: '-10%',
          left: '-10%',
          background: 'radial-gradient(circle, var(--aura-color-1) 0%, transparent 70%)',
          filter: 'blur(120px)',
          opacity: 0.18,
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: '40vw',
          height: '40vw',
          bottom: '-10%',
          right: '-5%',
          background: 'radial-gradient(circle, var(--aura-color-2) 0%, transparent 70%)',
          filter: 'blur(120px)',
          opacity: 0.18,
        }}
      />
    </div>
  );
}

function AuraBackgroundWithTracking({
  containerRef,
}: {
  containerRef: React.RefObject<HTMLDivElement | null>;
}) {
  useMouseAura(containerRef);

  return (
    <div ref={containerRef} className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <div
        className="aura-1 absolute rounded-full"
        style={{
          width: '70vw',
          height: '70vw',
          top: '-20%',
          left: '-10%',
          background: 'radial-gradient(circle, var(--aura-color-1) 0%, transparent 70%)',
          filter: 'blur(120px)',
          opacity: 0.4,
        }}
      />
      <div
        className="aura-2 absolute rounded-full"
        style={{
          width: '50vw',
          height: '50vw',
          bottom: '-10%',
          right: '-10%',
          background: 'radial-gradient(circle, var(--aura-color-2) 0%, transparent 70%)',
          filter: 'blur(120px)',
          opacity: 0.4,
        }}
      />
      <div
        className="aura-3 absolute rounded-full pointer-events-none"
        style={{
          width: '40vw',
          height: '40vw',
          transform: 'translate(-50%, -50%)',
          left: 'var(--aura-x, 50%)',
          top: 'var(--aura-y, 50%)',
          background: 'radial-gradient(circle, var(--aura-color-2) 0%, transparent 70%)',
          filter: 'blur(80px)',
          opacity: 0.25,
          transition:
            'left 0.8s cubic-bezier(0.23, 1, 0.32, 1), top 0.8s cubic-bezier(0.23, 1, 0.32, 1)',
        }}
      />
    </div>
  );
}
