import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TASK_FEEDBACK_LABELS,
  TASK_LABELS,
  TASK_STATE_LABELS,
  TASK_STATUS_LABELS,
  TOAST_MESSAGES,
} from '@/constants/labels';
import { TaskCard } from '@/components/ui/TaskCard';
import { triggerTask, terminateTaskRun, extractApiErrorMessage } from '@/services/taskService';
import { useDrawerStore } from '@/stores/drawerStore';
import { useTaskStore } from '@/stores/taskStore';
import { useToastStore } from '@/stores/toastStore';
import type { Task, TaskStatus } from '@/types/task';
import {
  Button,
  ContentSection,
  ControlToolbar,
  ControlToolbarActions,
  ControlToolbarMain,
  CustomSelect,
  InputBox,
  KpiCard,
} from '@vistaflow/ui';

type TaskFilter = 'all' | TaskStatus;

const statusOptions: Array<{ value: TaskFilter; label: string }> = [
  { value: 'all', label: TASK_LABELS.allStatus },
  { value: 'idle', label: TASK_STATUS_LABELS.idle },
  { value: 'running', label: TASK_STATUS_LABELS.running },
  { value: 'pending', label: TASK_STATUS_LABELS.pending },
  { value: 'completed', label: TASK_STATUS_LABELS.completed },
  { value: 'error', label: TASK_STATUS_LABELS.error },
  { value: 'terminated', label: TASK_STATUS_LABELS.terminated },
];

export default function TasksView() {
  const queryClient = useQueryClient();
  const tasks = useTaskStore((state) => state.tasks);
  const addToast = useToastStore((state) => state.addToast);
  const openTaskDrawer = useDrawerStore((state) => state.openTaskDrawer);
  const openTaskDetailDrawer = useDrawerStore((state) => state.openTaskDetailDrawer);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskFilter>('all');

  const runTaskMutation = useMutation({
    mutationFn: (task: Task) => triggerTask(task.id),
    onSuccess: async (_run, task) => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'tasks'] });
      await queryClient.invalidateQueries({ queryKey: ['admin', 'task', task.id] });
      await queryClient.invalidateQueries({ queryKey: ['admin', 'task-runs', task.id] });
      addToast(
        task.status === 'idle' ? TASK_FEEDBACK_LABELS.taskQueued : TOAST_MESSAGES.taskRestarted,
        'success',
      );
    },
    onError: (error: unknown) => {
      addToast(extractApiErrorMessage(error), 'error');
    },
  });

  const terminateTaskMutation = useMutation({
    mutationFn: (task: Task) => terminateTaskRun(task.latestRun!.id),
    onSuccess: async (_run, task) => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'tasks'] });
      await queryClient.invalidateQueries({ queryKey: ['admin', 'task', task.id] });
      await queryClient.invalidateQueries({ queryKey: ['admin', 'task-runs', task.id] });
      await queryClient.invalidateQueries({ queryKey: ['admin', 'task-run-logs'] });
      addToast(TOAST_MESSAGES.taskTerminated, 'warn');
    },
    onError: (error: unknown) => {
      addToast(extractApiErrorMessage(error), 'error');
    },
  });

  const runningCount = tasks.filter((task) => task.status === 'running').length;
  const pendingCount = tasks.filter((task) => task.status === 'pending').length;
  const errorCount = tasks.filter((task) => task.status === 'error' || task.status === 'terminated').length;

  const filteredTasks = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return tasks.filter((task) => {
      const searchableFields = [task.name, task.typeLabel, task.description ?? '', task.type];
      const matchesKeyword =
        keyword.length === 0 ||
        searchableFields.some((field) => field.toLowerCase().includes(keyword));
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      return matchesKeyword && matchesStatus;
    });
  }, [search, statusFilter, tasks]);

  const busyTaskId = runTaskMutation.isPending
    ? runTaskMutation.variables.id
    : terminateTaskMutation.isPending
      ? terminateTaskMutation.variables.id
      : null;

  return (
    <div className="vf-page-stack">
      <ContentSection spacing="dense">
        <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
          <KpiCard
            label={TASK_LABELS.activeTotal}
            value={
              <>
                {runningCount + pendingCount} <span className="text-lg text-muted">/ {tasks.length}</span>
              </>
            }
          />
          <KpiCard
            label={TASK_LABELS.running}
            value={runningCount}
            accentColor="#4ADE80"
            valueClassName="text-[#4ADE80]"
          />
          <KpiCard
            label={TASK_STATE_LABELS.queuedKpi}
            value={pendingCount}
            accentColor="#FACC15"
            alertDot={pendingCount > 0}
            valueClassName="text-[#FACC15]"
          />
          <KpiCard
            label={TASK_LABELS.errorTerminated}
            value={errorCount}
            accentColor="#F87171"
            valueClassName="text-[#F87171]"
          />
        </div>
      </ContentSection>

      <ControlToolbar>
        <ControlToolbarMain>
          <InputBox
            placeholder={TASK_LABELS.searchPlaceholder}
            className="min-w-0 w-full"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </ControlToolbarMain>
        <ControlToolbarActions>
          <CustomSelect
            options={statusOptions}
            value={statusFilter}
            onChange={(value) => setStatusFilter(value as TaskFilter)}
            className="w-full md:w-[180px]"
          />
          <Button variant="primary" size="sm" onClick={openTaskDrawer}>
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {TASK_LABELS.newTask}
          </Button>
        </ControlToolbarActions>
      </ControlToolbar>

      <ContentSection spacing="dense">
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onTerminate={(selectedTask) => terminateTaskMutation.mutate(selectedTask)}
              onRun={(selectedTask) => runTaskMutation.mutate(selectedTask)}
              onShowDetails={(selectedTask) => openTaskDetailDrawer(selectedTask.id)}
              actionDisabled={busyTaskId === task.id}
            />
          ))}
        </div>
      </ContentSection>
    </div>
  );
}
