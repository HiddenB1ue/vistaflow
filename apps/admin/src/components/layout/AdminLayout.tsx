import { useEffect, useCallback } from 'react';
import { useViewStore } from '@/stores/viewStore';
import { useTaskStore } from '@/stores/taskStore';
import { useUiStore } from '@/stores/uiStore';
import { VIEW_CONFIGS } from '@/types/view';
import type { ViewId } from '@/types/view';
import { useViewTransition } from '@/hooks/useViewTransition';

import { AuraBackground, NoiseTexture, ToastContainer, DrawerBackdrop } from '@vistaflow/ui';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { TaskDrawer } from '@/components/overlays/TaskDrawer';
import { StationDrawer } from '@/components/overlays/StationDrawer';
import { PreviewModal } from '@/components/overlays/PreviewModal';

import { OverviewView } from '@/pages/OverviewView';
import { TasksView } from '@/pages/TasksView';
import { DataView } from '@/pages/DataView';
import { ConfigView } from '@/pages/ConfigView';
import { LogView } from '@/pages/LogView';

export function AdminLayout() {
  const activeView = useViewStore((s) => s.activeView);
  const switchView = useViewStore((s) => s.switchView);
  const tasks = useTaskStore((s) => s.tasks);
  const updateTaskStatus = useTaskStore((s) => s.updateTaskStatus);
  const toasts = useUiStore((s) => s.toasts);
  const removeToast = useUiStore((s) => s.removeToast);
  const addToast = useUiStore((s) => s.addToast);
  const taskDrawerOpen = useUiStore((s) => s.taskDrawerOpen);
  const stationDrawerOpen = useUiStore((s) => s.stationDrawerOpen);
  const stationDrawerData = useUiStore((s) => s.stationDrawerData);
  const previewModalOpen = useUiStore((s) => s.previewModalOpen);
  const openTaskDrawer = useUiStore((s) => s.openTaskDrawer);
  const closeTaskDrawer = useUiStore((s) => s.closeTaskDrawer);
  const closeStationDrawer = useUiStore((s) => s.closeStationDrawer);
  const openStationDrawer = useUiStore((s) => s.openStationDrawer);
  const openPreviewModal = useUiStore((s) => s.openPreviewModal);
  const closePreviewModal = useUiStore((s) => s.closePreviewModal);

  const { containerRef, animateIn } = useViewTransition();

  const viewConfig = VIEW_CONFIGS[activeView];
  const pendingTaskCount = tasks.filter((t) => t.status === 'pending').length;

  const handleNavigate = useCallback(
    (viewId: ViewId) => {
      switchView(viewId);
    },
    [switchView],
  );

  useEffect(() => {
    animateIn();
  }, [activeView, animateIn]);

  const handleRefresh = useCallback(() => {
    addToast('数据已刷新', 'info');
  }, [addToast]);

  const handleStopTask = useCallback(
    (taskId: string) => {
      updateTaskStatus(taskId, 'terminated');
      addToast('任务已强制终止', 'error');
    },
    [updateTaskStatus, addToast],
  );

  const handleRestartTask = useCallback(
    (taskId: string) => {
      updateTaskStatus(taskId, 'running');
      addToast('任务已重新加入执行队列', 'success');
    },
    [updateTaskStatus, addToast],
  );

  const handlePreviewTask = useCallback(() => {
    openPreviewModal();
  }, [openPreviewModal]);

  const handleNewTask = useCallback(() => {
    openTaskDrawer();
  }, [openTaskDrawer]);

  const handleTaskDrawerSubmit = useCallback(
    (taskName: string) => {
      closeTaskDrawer();
      addToast(`任务「${taskName}」已成功下发`, 'success');
    },
    [closeTaskDrawer, addToast],
  );

  const handleStationSave = useCallback(() => {
    closeStationDrawer();
    addToast('站点信息已保存', 'success');
  }, [closeStationDrawer, addToast]);

  const handleStationDelete = useCallback(() => {
    closeStationDrawer();
    addToast('站点数据已删除', 'error');
  }, [closeStationDrawer, addToast]);

  const handlePreviewConfirm = useCallback(() => {
    closePreviewModal();
    addToast('3条数据已确认写入', 'success');
  }, [closePreviewModal, addToast]);

  const handleNavigateToConfig = useCallback(() => {
    switchView('view-config');
    addToast('请先更新代理凭证', 'warn');
  }, [switchView, addToast]);

  const handleCloseBackdrop = useCallback(() => {
    closeTaskDrawer();
    closeStationDrawer();
  }, [closeTaskDrawer, closeStationDrawer]);

  // Escape key handler for drawers
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (taskDrawerOpen) closeTaskDrawer();
        if (stationDrawerOpen) closeStationDrawer();
        if (previewModalOpen) closePreviewModal();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [taskDrawerOpen, stationDrawerOpen, previewModalOpen, closeTaskDrawer, closeStationDrawer, closePreviewModal]);

  const renderView = () => {
    switch (activeView) {
      case 'view-overview':
        return <OverviewView onNavigateToTasks={() => handleNavigate('view-tasks')} onNavigateToLog={() => handleNavigate('view-log')} />;
      case 'view-tasks':
        return (
          <TasksView
            tasks={tasks}
            onStop={handleStopTask}
            onRestart={handleRestartTask}
            onPreview={handlePreviewTask}
            onNewTask={handleNewTask}
            onNavigateToConfig={handleNavigateToConfig}
            addToast={addToast}
          />
        );
      case 'view-data':
        return <DataView onEditStation={openStationDrawer} addToast={addToast} />;
      case 'view-config':
        return <ConfigView addToast={addToast} />;
      case 'view-log':
        return <LogView addToast={addToast} />;
      default:
        return null;
    }
  };

  return (
    <>
      <AuraBackground />
      <NoiseTexture opacity={0.03} />
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
      <DrawerBackdrop isActive={taskDrawerOpen || stationDrawerOpen} onClick={handleCloseBackdrop} />
      <TaskDrawer isOpen={taskDrawerOpen} onClose={closeTaskDrawer} onSubmit={handleTaskDrawerSubmit} />
      <StationDrawer
        isOpen={stationDrawerOpen}
        station={stationDrawerData}
        onClose={closeStationDrawer}
        onSave={handleStationSave}
        onDelete={handleStationDelete}
      />
      <PreviewModal isOpen={previewModalOpen} onClose={closePreviewModal} onConfirm={handlePreviewConfirm} />

      <div className="flex h-screen overflow-hidden text-starlight">
        <Sidebar activeView={activeView} pendingTaskCount={pendingTaskCount} onNavigate={handleNavigate} />
        <main className="flex-1 relative z-10 overflow-y-auto h-full">
          <Header title={viewConfig.title} subtitle={viewConfig.subtitle} onRefresh={handleRefresh} timestamp="03-30 12:04:32" />
          <div className="p-8" ref={containerRef}>
            {renderView()}
          </div>
        </main>
      </div>
    </>
  );
}
