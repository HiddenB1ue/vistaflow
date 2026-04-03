type StatusDotVariant = 'running' | 'pending' | 'idle' | 'error';

interface StatusDotProps {
  variant: StatusDotVariant;
}

const classMap: Record<StatusDotVariant, string> = {
  running: 'status-running',
  pending: 'status-pending',
  idle: 'status-idle',
  error: 'status-error',
};

export function StatusDot({ variant }: StatusDotProps) {
  return <span className={`status-dot ${classMap[variant]}`} />;
}
