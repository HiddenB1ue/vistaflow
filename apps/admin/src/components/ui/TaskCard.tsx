import type { Task } from '@/types/task';
import { StatusDot } from './StatusDot';
import { Badge } from './Badge';
import { Button } from './Button';

interface TaskCardProps {
  task: Task;
  onStop?: (taskId: string) => void;
  onRestart?: (taskId: string) => void;
  onPreview?: (taskId: string) => void;
  onNavigateToConfig?: () => void;
  onShowDetails?: (taskId: string) => void;
}

const dotVariantMap: Record<string, 'running' | 'pending' | 'idle' | 'error'> = {
  running: 'running',
  pending: 'pending',
  completed: 'idle',
  error: 'error',
  terminated: 'error',
};

const badgeVariantMap: Record<string, 'green' | 'yellow' | 'blue' | 'red'> = {
  running: 'green',
  pending: 'yellow',
  completed: 'blue',
  error: 'red',
  terminated: 'red',
};

const badgeLabelMap: Record<string, string> = {
  running: 'Running',
  pending: 'Pending Confirm',
  completed: 'Completed',
  error: 'Error',
  terminated: 'Terminated',
};

export function TaskCard({ task, onStop, onRestart, onPreview, onNavigateToConfig, onShowDetails }: TaskCardProps) {
  const isPending = task.status === 'pending';
  const isError = task.status === 'error';
  const isCompleted = task.status === 'completed';
  const isRunning = task.status === 'running';

  let cardClassName = 'glass-panel p-5 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5';
  if (isPending) cardClassName += ' border border-[#FACC15]/25 bg-[#FACC15]/[0.04]';
  if (isError) cardClassName += ' border border-[#F87171]/20 bg-[#F87171]/[0.03] opacity-80';
  if (isCompleted) cardClassName += ' opacity-70';

  return (
    <div className={cardClassName}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <StatusDot variant={dotVariantMap[task.status] ?? 'idle'} />
          <Badge variant={badgeVariantMap[task.status] ?? 'blue'}>{badgeLabelMap[task.status] ?? task.status}</Badge>
          <span className="text-[10px] text-[#8A8A8E] font-display tracking-widest uppercase">{task.typeLabel}</span>
        </div>
        <h3 className="font-serif text-xl tracking-wide mb-1 truncate">{task.name}</h3>
        <div className="text-xs text-[#8A8A8E]">
          {task.errorMessage ? (
            <span className="text-red-400/70">{task.errorMessage}</span>
          ) : (
            task.description
          )}
        </div>
      </div>

      <div className={`${isPending ? '' : 'flex gap-6'} border-l border-white/[0.08] pl-6 shrink-0`}>
        <div>
          <div className="text-[10px] text-[#8A8A8E] tracking-widest uppercase mb-1">{task.metrics.label}</div>
          <div className={`text-sm font-display ${isPending ? 'text-[#FACC15] font-medium' : ''}`}>{task.metrics.value}</div>
        </div>
        {!isPending && (
          <div>
            <div className="text-[10px] text-[#8A8A8E] tracking-widest uppercase mb-1">{task.timing.label}</div>
            <div className={`text-sm font-mono ${isRunning ? 'text-[#4ADE80]' : isError ? 'text-[#F87171]' : ''}`}>{task.timing.value}</div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {isRunning && (
          <>
            <Button variant="danger" size="sm" onClick={() => onStop?.(task.id)}>终止</Button>
            <Button variant="outline" size="sm" onClick={() => onShowDetails?.(task.id)}>详情</Button>
          </>
        )}
        {isPending && (
          <Button variant="warning" onClick={() => onPreview?.(task.id)}>预览并确认</Button>
        )}
        {isCompleted && (
          <Button variant="outline" size="sm" onClick={() => onRestart?.(task.id)}>重新执行</Button>
        )}
        {isError && (
          <Button variant="outline" size="sm" onClick={() => onNavigateToConfig?.()}>去修复</Button>
        )}
      </div>
    </div>
  );
}
