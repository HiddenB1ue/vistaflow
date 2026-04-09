import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Outlet, useLocation } from 'react-router-dom';
import { AuraBackground, DrawerBackdrop, ErrorBoundary, NoiseTexture, ToastContainer } from '@vistaflow/ui';
import { TaskDetailDrawer } from '@/components/overlays/TaskDetailDrawer';
import { TaskDrawer } from '@/components/overlays/TaskDrawer';
import { ROUTE_META_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import { fetchTasks } from '@/services/taskService';
import { useDrawerStore } from '@/stores/drawerStore';
import { useTaskStore } from '@/stores/taskStore';
import { useToastStore } from '@/stores/toastStore';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

const ROUTE_META = {
  '/': ROUTE_META_LABELS.overview,
  '/tasks': ROUTE_META_LABELS.tasks,
  '/data': ROUTE_META_LABELS.data,
  '/config': ROUTE_META_LABELS.config,
  '/log': ROUTE_META_LABELS.log,
} as const;

function formatTimestamp(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date).replace(/\//g, '-');
}

export function AdminLayout() {
  const queryClient = useQueryClient();
  const mainRef = useRef<HTMLElement | null>(null);
  const location = useLocation();
  const [headerScrolled, setHeaderScrolled] = useState(false);
  const tasks = useTaskStore((state) => state.tasks);
  const setTasks = useTaskStore((state) => state.setTasks);
  const toasts = useToastStore((state) => state.toasts);
  const removeToast = useToastStore((state) => state.removeToast);
  const addToast = useToastStore((state) => state.addToast);
  const taskDrawerOpen = useDrawerStore((state) => state.taskDrawerOpen);
  const taskDetailDrawerOpen = useDrawerStore((state) => state.taskDetailDrawerOpen);
  const taskDetailDrawerTaskId = useDrawerStore((state) => state.taskDetailDrawerTaskId);
  const closeTaskDrawer = useDrawerStore((state) => state.closeTaskDrawer);
  const closeTaskDetailDrawer = useDrawerStore((state) => state.closeTaskDetailDrawer);

  const meta = ROUTE_META[location.pathname as keyof typeof ROUTE_META] ?? ROUTE_META['/'];
  const pendingTaskCount = tasks.filter((task) => task.status === 'pending').length;
  const timestamp = useMemo(() => formatTimestamp(new Date()), []);

  const { data: taskData, refetch: refetchTasks } = useQuery({
    queryKey: ['admin', 'tasks'],
    queryFn: fetchTasks,
  });

  useEffect(() => {
    if (taskData) {
      setTasks(taskData);
    }
  }, [setTasks, taskData]);

  const handleRefresh = useCallback(async () => {
    await Promise.all([
      refetchTasks(),
      queryClient.invalidateQueries({ queryKey: ['admin', 'data'] }),
      queryClient.invalidateQueries({ queryKey: ['admin', 'system'] }),
    ]);
    addToast(TOAST_MESSAGES.dataRefreshed, 'info');
  }, [addToast, queryClient, refetchTasks]);

  const handleTaskDrawerSubmit = useCallback((taskName: string) => {
    closeTaskDrawer();
    addToast(TOAST_MESSAGES.taskCreated(taskName), 'success');
  }, [addToast, closeTaskDrawer]);

  const handleCloseBackdrop = useCallback(() => {
    closeTaskDrawer();
    closeTaskDetailDrawer();
  }, [closeTaskDetailDrawer, closeTaskDrawer]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      if (taskDrawerOpen) closeTaskDrawer();
      if (taskDetailDrawerOpen) closeTaskDetailDrawer();
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [closeTaskDetailDrawer, closeTaskDrawer, taskDetailDrawerOpen, taskDrawerOpen]);

  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    const handleScroll = () => {
      setHeaderScrolled(main.scrollTop > 12);
    };

    handleScroll();
    main.addEventListener('scroll', handleScroll, { passive: true });
    return () => main.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <AuraBackground enableMouseTracking />
      <NoiseTexture opacity={0.03} />
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
      <DrawerBackdrop isActive={taskDrawerOpen || taskDetailDrawerOpen} onClick={handleCloseBackdrop} />
      <TaskDrawer isOpen={taskDrawerOpen} onClose={closeTaskDrawer} onSubmit={handleTaskDrawerSubmit} />
      <TaskDetailDrawer
        isOpen={taskDetailDrawerOpen}
        taskId={taskDetailDrawerTaskId}
        onClose={closeTaskDetailDrawer}
      />

      <div className="flex h-screen overflow-hidden text-starlight">
        <Sidebar pendingTaskCount={pendingTaskCount} />
        <main ref={mainRef} className="relative z-10 h-full flex-1 overflow-y-auto">
          <Header title={meta.title} subtitle={meta.subtitle} onRefresh={handleRefresh} timestamp={timestamp} scrolled={headerScrolled} />
          <div className="vf-page-frame">
            <div className="vf-content-section vf-content-section--default vf-content-section--width-wide">
              <ErrorBoundary>
                <Outlet />
              </ErrorBoundary>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
