import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Badge,
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalShell,
  PanelCard,
} from '@vistaflow/ui';
import {
  COMMON_LABELS,
  TASK_DETAIL_LABELS,
  TASK_LABELS,
  TASK_RESULT_LABELS,
  TASK_STATE_LABELS,
  TASK_STATUS_LABELS,
} from '@/constants/labels';
import { fetchTask, fetchTaskRunLogs, fetchTaskRuns } from '@/services/taskService';
import type { TaskRunLog } from '@/types/task';
import { formatTaskSchedule } from '@/utils/taskSchedule';

interface TaskDetailDrawerProps {
  isOpen: boolean;
  taskId: number | null;
  onClose: () => void;
  onDelete?: (taskId: number) => void;
  deleteDisabled?: boolean;
}

function formatDateTime(value?: string | null): string {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

function formatJson(value: Record<string, unknown>): string {
  return JSON.stringify(value, null, 2);
}

function statusLabel(status: string): string {
  switch (status) {
    case 'idle':
      return TASK_STATUS_LABELS.idle;
    case 'pending':
      return TASK_STATUS_LABELS.pending;
    case 'running':
      return TASK_STATUS_LABELS.running;
    case 'completed':
      return TASK_STATUS_LABELS.completed;
    case 'error':
      return TASK_STATUS_LABELS.error;
    case 'terminated':
      return TASK_STATUS_LABELS.terminated;
    default:
      return status;
  }
}

function statusVariant(status: string): 'green' | 'yellow' | 'blue' | 'red' {
  switch (status) {
    case 'running':
      return 'green';
    case 'pending':
      return 'yellow';
    case 'error':
    case 'terminated':
      return 'red';
    default:
      return 'blue';
  }
}

function resultLabel(resultLevel?: string | null): string {
  switch (resultLevel) {
    case 'success':
      return TASK_RESULT_LABELS.success;
    case 'warning':
      return TASK_RESULT_LABELS.warning;
    case 'error':
      return TASK_RESULT_LABELS.error;
    default:
      return '-';
  }
}

function severityVariant(severity: TaskRunLog['severity']): 'green' | 'yellow' | 'blue' | 'red' {
  switch (severity) {
    case 'SUCCESS':
      return 'green';
    case 'WARN':
      return 'yellow';
    case 'ERROR':
      return 'red';
    default:
      return 'blue';
  }
}



export function TaskDetailDrawer({
  isOpen,
  taskId,
  onClose,
  onDelete,
  deleteDisabled = false,
}: TaskDetailDrawerProps) {
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const { data: task, isLoading: taskLoading } = useQuery({
    queryKey: ['admin', 'task', taskId],
    queryFn: () => fetchTask(taskId!),
    enabled: isOpen && taskId !== null,
  });

  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ['admin', 'task-runs', taskId],
    queryFn: () => fetchTaskRuns(taskId!),
    enabled: isOpen && taskId !== null,
  });

  const runs = runsData?.items ?? [];

  useEffect(() => {
    if (!isOpen) {
      setSelectedRunId(null);
      return;
    }

    if (!task) {
      return;
    }

    if (!runs.length) {
      setSelectedRunId(task.latestRun?.id ?? null);
      return;
    }

    const hasSelectedRun = selectedRunId !== null && runs.some((run) => run.id === selectedRunId);
    if (hasSelectedRun) {
      return;
    }

    setSelectedRunId(task.latestRun?.id ?? runs[0]?.id ?? null);
  }, [isOpen, runs, selectedRunId, task]);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ['admin', 'task-run-logs', selectedRunId],
    queryFn: () => fetchTaskRunLogs(selectedRunId!),
    enabled: isOpen && selectedRunId !== null,
  });

  useEffect(() => {
    if (!isOpen) {
      setDeleteConfirmOpen(false);
    }
  }, [isOpen]);

  return (
    <>
      <DrawerShell open={isOpen}>
        <DrawerHeader
          eyebrow={TASK_DETAIL_LABELS.eyebrow}
          title={task?.name ?? TASK_LABELS.details}
          subtitle={task ? TASK_DETAIL_LABELS.subtitle(task.typeLabel) : ''}
          onClose={onClose}
          closeLabel={COMMON_LABELS.close}
        />

        <DrawerBody>
        {taskLoading && !task ? (
          <div className="vf-drawer-meta">{TASK_DETAIL_LABELS.loadingTask}</div>
        ) : null}

        {task ? (
          <>
            <section className="vf-drawer-group">
              <PanelCard className="gap-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={statusVariant(task.status)}>{statusLabel(task.status)}</Badge>
                  {!task.enabled ? <Badge variant="red">{TASK_STATE_LABELS.disabled}</Badge> : null}
                  <span className="text-xs uppercase tracking-wide text-muted">{task.typeLabel}</span>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <div className="vf-drawer-label">{TASK_DETAIL_LABELS.description}</div>
                    <div className="vf-drawer-meta mt-2">{task.description || TASK_STATE_LABELS.noDescription}</div>
                  </div>
                  <div>
                    <div className="vf-drawer-label">{TASK_DETAIL_LABELS.cron}</div>
                    <div className="vf-drawer-meta mt-2">{formatTaskSchedule(task)}</div>
                  </div>
                  <div>
                    <div className="vf-drawer-label">{TASK_DETAIL_LABELS.enabled}</div>
                    <div className="vf-drawer-meta mt-2">
                      {task.enabled ? TASK_DETAIL_LABELS.enabledYes : TASK_DETAIL_LABELS.enabledNo}
                    </div>
                  </div>
                  <div>
                    <div className="vf-drawer-label">{TASK_DETAIL_LABELS.currentConfig}</div>
                    <pre className="mt-2 overflow-x-auto rounded border border-white/10 bg-black/20 p-3 text-xs text-muted">
                      {formatJson(task.payload)}
                    </pre>
                  </div>
                </div>
              </PanelCard>
            </section>

            <section className="vf-drawer-group">
              <div className="vf-drawer-label mb-3">{TASK_DETAIL_LABELS.executionHistory}</div>
              {runsLoading ? (
                <div className="vf-drawer-meta">{TASK_DETAIL_LABELS.loadingRuns}</div>
              ) : runs.length === 0 ? (
                <div className="vf-drawer-meta">{TASK_DETAIL_LABELS.noRuns}</div>
              ) : (
                <div className="space-y-3">
                  {runs.map((run) => (
                    <PanelCard key={run.id} className={selectedRunId === run.id ? 'border border-[#8B5CF6]/30' : ''}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant={statusVariant(run.status)}>{statusLabel(run.status)}</Badge>
                            <span className="text-sm font-display">#{run.id}</span>
                          </div>
                          <div className="grid gap-2 text-xs text-muted md:grid-cols-2">
                            <span>{TASK_DETAIL_LABELS.runStarted}: {formatDateTime(run.startedAt)}</span>
                            <span>{TASK_DETAIL_LABELS.runFinished}: {formatDateTime(run.finishedAt)}</span>
                            <span>{TASK_DETAIL_LABELS.runRequestedBy}: {run.requestedBy}</span>
                            <span>{TASK_DETAIL_LABELS.runResult}: {resultLabel(run.resultLevel)}</span>
                          </div>
                          {run.summary ? (
                            <div className="text-xs text-muted">{TASK_DETAIL_LABELS.runSummary}: {run.summary}</div>
                          ) : null}
                          {run.errorMessage ? (
                            <div className="text-xs text-red-300">{TASK_DETAIL_LABELS.runError}: {run.errorMessage}</div>
                          ) : null}
                          {run.terminationReason ? (
                            <div className="text-xs text-red-300">{TASK_DETAIL_LABELS.runTermination}: {run.terminationReason}</div>
                          ) : null}
                          <div className="text-xs text-muted">{TASK_DETAIL_LABELS.runMetrics}: {run.metricsValue || '-'}</div>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => setSelectedRunId(run.id)}>
                          {TASK_DETAIL_LABELS.selectRun}
                        </Button>
                      </div>
                    </PanelCard>
                  ))}
                </div>
              )}
            </section>

            <section className="vf-drawer-group">
              <div className="vf-drawer-label mb-3">{TASK_DETAIL_LABELS.executionLogs}</div>
              {selectedRun ? (
                <div className="mb-3 text-xs text-muted">{TASK_STATE_LABELS.latestRun(selectedRun.id)}</div>
              ) : null}
              {logsLoading ? (
                <div className="vf-drawer-meta">{TASK_DETAIL_LABELS.loadingLogs}</div>
              ) : !logs || logs.length === 0 ? (
                <div className="vf-drawer-meta">{TASK_DETAIL_LABELS.noLogs}</div>
              ) : (
                <div className="space-y-3">
                  {logs.map((log) => (
                    <PanelCard key={log.id}>
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant={severityVariant(log.severity)}>{log.severity}</Badge>
                            <span className="text-xs text-muted">
                              {TASK_DETAIL_LABELS.logTime}: {formatDateTime(log.createdAt)}
                            </span>
                          </div>
                          <div className="text-sm">{log.message}</div>
                        </div>
                        <div className="text-xs uppercase tracking-wide text-muted">
                          {TASK_DETAIL_LABELS.logSeverity}: {log.severity}
                        </div>
                      </div>
                    </PanelCard>
                  ))}
                </div>
              )}
            </section>
          </>
        ) : null}
        </DrawerBody>

        <DrawerFooter align="between">
          <Button
            variant="danger"
            onClick={() => setDeleteConfirmOpen(true)}
            disabled={!task || deleteDisabled}
          >
            删除任务
          </Button>
          <Button variant="outline" onClick={onClose}>
            {COMMON_LABELS.close}
          </Button>
        </DrawerFooter>
      </DrawerShell>

      <ModalShell
        open={deleteConfirmOpen}
        size="sm"
        onBackdropClick={() => setDeleteConfirmOpen(false)}
      >
        <ModalHeader
          title="删除任务"
          subtitle={task ? `确认删除“${task.name}”？历史执行记录也会随任务移除。` : ''}
          onClose={() => setDeleteConfirmOpen(false)}
          closeLabel={COMMON_LABELS.close}
        />
        <ModalBody>
          <div className="text-sm text-muted">
            如果任务正在排队或运行中，后端会拒绝删除。需要关闭循环调度时，请优先在列表中停用任务。
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)} disabled={deleteDisabled}>
            {COMMON_LABELS.cancel}
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              if (task) {
                onDelete?.(task.id);
              }
            }}
            disabled={!task || deleteDisabled}
          >
            删除任务
          </Button>
        </ModalFooter>
      </ModalShell>
    </>
  );
}
