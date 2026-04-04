
import type { Task } from '@/types/task';
import { TASK_LABELS } from '@/constants/labels';
import { Badge, Button, PanelCard, StatusDot } from '@vistaflow/ui';

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
  running: TASK_LABELS.statusRunning,
  pending: TASK_LABELS.statusPending,
  completed: TASK_LABELS.statusDone,
  error: TASK_LABELS.statusError,
  terminated: TASK_LABELS.statusTerminated,
};

export function TaskCard({ task, onStop, onRestart, onPreview, onNavigateToConfig, onShowDetails }: TaskCardProps) {
  const isPending = task.status === 'pending';
  const isError = task.status === 'error';
  const isCompleted = task.status === 'completed';
  const isRunning = task.status === 'running';

  let cardClassName = '';
  if (isPending) cardClassName += ' border border-[#FACC15]/25 bg-[#FACC15]/[0.04]';
  if (isError) cardClassName += ' border border-[#F87171]/20 bg-[#F87171]/[0.03] opacity-80';
  if (isCompleted) cardClassName += ' opacity-70';

  return (
    <PanelCard className={cardClassName.trim()}>
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:gap-6 lg:grid-cols-[minmax(0,1fr)_auto_auto] lg:items-center">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <StatusDot variant={dotVariantMap[task.status] ?? 'idle'} />
            <Badge variant={badgeVariantMap[task.status] ?? 'blue'}>{badgeLabelMap[task.status] ?? task.status}</Badge>
            <span className="text-[10px] font-display uppercase tracking-widest text-[#8A8A8E]">{task.typeLabel}</span>
          </div>
          <h3 className="mb-1 truncate font-serif text-xl tracking-wide">{task.name}</h3>
          <div className="text-xs text-[#8A8A8E]">
            {task.errorMessage ? <span className="text-red-400/70">{task.errorMessage}</span> : task.description}
          </div>
        </div>

        <div className={`grid shrink-0 gap-4 border-t border-white/[0.08] pt-5 sm:grid-cols-2 md:min-w-[220px] md:border-l md:border-t-0 md:pl-6 md:pt-0 md:grid-cols-1 lg:min-w-[260px] lg:grid-cols-2 ${isPending ? 'sm:grid-cols-1 lg:grid-cols-1' : ''}`}>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-widest text-[#8A8A8E]">{task.metrics.label}</div>
            <div className={`text-sm font-display ${isPending ? 'font-medium text-[#FACC15]' : ''}`}>{task.metrics.value}</div>
          </div>
          {!isPending && (
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-widest text-[#8A8A8E]">{task.timing.label}</div>
              <div className={`text-sm font-mono ${isRunning ? 'text-[#4ADE80]' : isError ? 'text-[#F87171]' : ''}`}>{task.timing.value}</div>
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2 md:col-span-2 md:justify-end lg:col-span-1">
          {isRunning && (
            <>
              <Button variant="danger" size="sm" onClick={() => onStop?.(task.id)}>{TASK_LABELS.stop}</Button>
              <Button variant="outline" size="sm" onClick={() => onShowDetails?.(task.id)}>{TASK_LABELS.details}</Button>
            </>
          )}
          {isPending && <Button variant="warning" size="sm" onClick={() => onPreview?.(task.id)}>{TASK_LABELS.previewConfirm}</Button>}
          {isCompleted && <Button variant="outline" size="sm" onClick={() => onRestart?.(task.id)}>{TASK_LABELS.restart}</Button>}
          {isError && <Button variant="outline" size="sm" onClick={() => onNavigateToConfig?.()}>{TASK_LABELS.goFix}</Button>}
        </div>
      </div>
    </PanelCard>
  );
}
