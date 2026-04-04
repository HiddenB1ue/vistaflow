
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TASK_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import { TaskCard } from '@/components/ui/TaskCard';
import { useDrawerStore } from '@/stores/drawerStore';
import { useModalStore } from '@/stores/modalStore';
import { useTaskStore } from '@/stores/taskStore';
import { useToastStore } from '@/stores/toastStore';
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

const statusOptions = [
  { value: 'all', label: TASK_LABELS.allStatus },
  { value: 'running', label: TASK_LABELS.statusRunning },
  { value: 'pending', label: TASK_LABELS.statusPending },
  { value: 'completed', label: TASK_LABELS.statusDone },
  { value: 'error', label: TASK_LABELS.statusError },
  { value: 'terminated', label: TASK_LABELS.statusTerminated },
];

export default function TasksView() {
  const navigate = useNavigate();
  const tasks = useTaskStore((state) => state.tasks);
  const updateTaskStatus = useTaskStore((state) => state.updateTaskStatus);
  const addToast = useToastStore((state) => state.addToast);
  const openTaskDrawer = useDrawerStore((state) => state.openTaskDrawer);
  const openPreviewModal = useModalStore((state) => state.openPreviewModal);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const runningCount = tasks.filter((task) => task.status === 'running').length;
  const pendingCount = tasks.filter((task) => task.status === 'pending').length;
  const errorCount = tasks.filter((task) => task.status === 'error' || task.status === 'terminated').length;

  const filteredTasks = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return tasks.filter((task) => {
      const matchesKeyword = keyword.length === 0 || [task.name, task.typeLabel, task.description].some((field) => field.toLowerCase().includes(keyword));
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      return matchesKeyword && matchesStatus;
    });
  }, [search, statusFilter, tasks]);

  const handleStop = useCallback((taskId: string) => {
    updateTaskStatus(taskId, 'terminated');
    addToast(TOAST_MESSAGES.taskTerminated, 'error');
  }, [addToast, updateTaskStatus]);

  const handleRestart = useCallback((taskId: string) => {
    updateTaskStatus(taskId, 'running');
    addToast(TOAST_MESSAGES.taskRestarted, 'success');
  }, [addToast, updateTaskStatus]);

  const handleNavigateToConfig = useCallback(() => {
    navigate('/config');
    addToast(TOAST_MESSAGES.updateCredentialFirst, 'warn');
  }, [addToast, navigate]);

  return (
    <div className="vf-page-stack">
      <ContentSection spacing="dense">
        <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
          <KpiCard label={TASK_LABELS.activeTotal} value={<>{runningCount + pendingCount} <span className="text-lg text-muted">/ {tasks.length}</span></>} />
          <KpiCard label={TASK_LABELS.running} value={runningCount} accentColor="#4ADE80" valueClassName="text-[#4ADE80]" />
          <KpiCard label={TASK_LABELS.pendingConfirm} value={pendingCount} accentColor="#FACC15" alertDot={pendingCount > 0} valueClassName="text-[#FACC15]" />
          <KpiCard label={TASK_LABELS.errorTerminated} value={errorCount} accentColor="#F87171" valueClassName="text-[#F87171]" />
        </div>
      </ContentSection>

      <ControlToolbar>
        <ControlToolbarMain>
          <InputBox placeholder={TASK_LABELS.searchPlaceholder} className="min-w-0 w-full" value={search} onChange={(event) => setSearch(event.target.value)} />
        </ControlToolbarMain>
        <ControlToolbarActions>
          <CustomSelect options={statusOptions} value={statusFilter} onChange={setStatusFilter} className="w-full md:w-[180px]" />
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
              onStop={handleStop}
              onRestart={handleRestart}
              onPreview={() => openPreviewModal()}
              onNavigateToConfig={handleNavigateToConfig}
              onShowDetails={() => addToast(TASK_LABELS.taskDetailsInDev, 'info')}
            />
          ))}
        </div>
      </ContentSection>
    </div>
  );
}
