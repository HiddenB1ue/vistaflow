import { TASK_LABELS, TASK_STATE_LABELS, TASK_STATUS_LABELS } from '@/constants/labels';
import type { Task } from '@/types/task';
import { Badge, Button, PanelCard, StatusDot } from '@vistaflow/ui';

interface TaskCardProps {
  task: Task;
  onTerminate?: (task: Task) => void;
  onRun?: (task: Task) => void;
  onShowDetails?: (task: Task) => void;
  actionDisabled?: boolean;
}

const dotVariantMap: Record<string, 'running' | 'pending' | 'idle' | 'error'> = {
  idle: 'idle',
  running: 'running',
  pending: 'pending',
  completed: 'idle',
  error: 'error',
  terminated: 'error',
};

const badgeVariantMap: Record<string, 'green' | 'yellow' | 'blue' | 'red'> = {
  idle: 'blue',
  running: 'green',
  pending: 'yellow',
  completed: 'blue',
  error: 'red',
  terminated: 'red',
};

const badgeLabelMap: Record<string, string> = {
  idle: TASK_STATUS_LABELS.idle,
  running: TASK_STATUS_LABELS.running,
  pending: TASK_STATUS_LABELS.pending,
  completed: TASK_STATUS_LABELS.completed,
  error: TASK_STATUS_LABELS.error,
  terminated: TASK_STATUS_LABELS.terminated,
};

export function TaskCard({ task, onTerminate, onRun, onShowDetails, actionDisabled = false }: TaskCardProps) {
  const isPending = task.status === 'pending';
  const isError = task.status === 'error';
  const isCompleted = task.status === 'completed';
  const isRunning = task.status === 'running';
  const isIdle = task.status === 'idle';
  const isTerminated = task.status === 'terminated';
  const canTerminate = isRunning || isPending;
  const canRun = !canTerminate && task.enabled;
  const runLabel = isIdle ? TASK_STATE_LABELS.runNow : TASK_LABELS.restart;
  const description = task.errorMessage || task.description || TASK_STATE_LABELS.noDescription;
  const latestRunText = task.latestRun
    ? TASK_STATE_LABELS.latestRun(task.latestRun.id)
    : TASK_STATE_LABELS.noRuns;
  const scheduleText = task.cron ? `Cron: ${task.cron}` : TASK_STATE_LABELS.manualTrigger;

  let cardClassName = '';
  if (isPending) cardClassName += ' border border-[#FACC15]/25 bg-[#FACC15]/[0.04]';
  if (isError || isTerminated) cardClassName += ' border border-[#F87171]/20 bg-[#F87171]/[0.03]';
  if (isCompleted) cardClassName += ' opacity-80';

  return (
    <PanelCard className={cardClassName.trim()}>
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:gap-6 lg:grid-cols-[minmax(0,1fr)_auto_auto] lg:items-center">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <StatusDot variant={dotVariantMap[task.status] ?? 'idle'} />
            <Badge variant={badgeVariantMap[task.status] ?? 'blue'}>
              {badgeLabelMap[task.status] ?? task.status}
            </Badge>
            {!task.enabled ? <Badge variant="red">{TASK_STATE_LABELS.disabled}</Badge> : null}
            <span className="text-[10px] font-display uppercase tracking-widest text-[#8A8A8E]">
              {task.typeLabel}
            </span>
          </div>
          <h3 className="mb-1 truncate font-serif text-xl tracking-wide">{task.name}</h3>
          <div className="text-xs text-[#8A8A8E]">{description}</div>
          <div className="mt-2 flex flex-wrap gap-3 text-[11px] uppercase tracking-wide text-[#6F6F73]">
            <span>{scheduleText}</span>
            <span>{latestRunText}</span>
          </div>
        </div>

        <div className={`grid shrink-0 gap-4 border-t border-white/[0.08] pt-5 sm:grid-cols-2 md:min-w-[220px] md:border-l md:border-t-0 md:pl-6 md:pt-0 md:grid-cols-1 lg:min-w-[260px] lg:grid-cols-2 ${isPending ? 'sm:grid-cols-1 lg:grid-cols-1' : ''}`}>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-widest text-[#8A8A8E]">
              {task.metrics.label}
            </div>
            <div className={`text-sm font-display ${isPending ? 'font-medium text-[#FACC15]' : ''}`}>
              {task.metrics.value || '-'}
            </div>
          </div>
          {!isPending && (
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-widest text-[#8A8A8E]">
                {task.timing.label}
              </div>
              <div className={`text-sm font-mono ${isRunning ? 'text-[#4ADE80]' : isError || isTerminated ? 'text-[#F87171]' : ''}`}>
                {task.timing.value || '-'}
              </div>
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2 md:col-span-2 md:justify-end lg:col-span-1">
          {canTerminate ? (
            <Button
              variant="danger"
              size="sm"
              onClick={() => onTerminate?.(task)}
              disabled={actionDisabled || !task.latestRun}
            >
              {TASK_LABELS.stop}
            </Button>
          ) : null}
          {canRun ? (
            <Button variant="outline" size="sm" onClick={() => onRun?.(task)} disabled={actionDisabled}>
              {runLabel}
            </Button>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onShowDetails?.(task)}
            disabled={actionDisabled}
          >
            {TASK_LABELS.details}
          </Button>
        </div>
      </div>
    </PanelCard>
  );
}
