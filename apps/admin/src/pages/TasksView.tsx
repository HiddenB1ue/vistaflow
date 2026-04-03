import { useState } from 'react';
import type { Task } from '@/types/task';
import type { ToastType } from '@/stores/uiStore';
import { KpiCard, InputBox, CustomSelect, Button } from '@vistaflow/ui';
import { TaskCard } from '@/components/ui/TaskCard';

interface TasksViewProps {
  tasks: Task[];
  onStop: (taskId: string) => void;
  onRestart: (taskId: string) => void;
  onPreview: (taskId: string) => void;
  onNewTask: () => void;
  onNavigateToConfig: () => void;
  addToast: (message: string, type: ToastType) => void;
}

const statusOptions = [
  { value: 'all', label: '所有状态' },
  { value: 'running', label: '执行中' },
  { value: 'pending', label: '待确认' },
  { value: 'done', label: '已完成' },
];

export function TasksView({ tasks, onStop, onRestart, onPreview, onNewTask, onNavigateToConfig, addToast }: TasksViewProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const runningCount = tasks.filter((t) => t.status === 'running').length;
  const pendingCount = tasks.filter((t) => t.status === 'pending').length;
  const errorCount = tasks.filter((t) => t.status === 'error').length;

  return (
    <div>
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard label="活跃 / 总计" value={<>{runningCount + pendingCount} <span className="text-lg text-muted">/ {tasks.length}</span></>} />
        <KpiCard label="执行中" value={runningCount} accentColor="#4ADE80" valueClassName="text-[#4ADE80]" />
        <KpiCard label="待人工确认" value={pendingCount} accentColor="#FACC15" alertDot={pendingCount > 0} valueClassName="text-[#FACC15]" />
        <KpiCard label="异常终止" value={errorCount} accentColor="#F87171" valueClassName="text-[#F87171]" />
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-6">
        <InputBox placeholder="搜索任务名称…" className="flex-1 min-w-48" value={search} onChange={(e) => setSearch(e.target.value)} />
        <CustomSelect options={statusOptions} value={statusFilter} onChange={setStatusFilter} className="w-40" />
        <Button variant="primary" onClick={onNewTask}>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建任务
        </Button>
      </div>

      {/* Task cards */}
      <div className="space-y-3">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onStop={onStop}
            onRestart={onRestart}
            onPreview={onPreview}
            onNavigateToConfig={onNavigateToConfig}
            onShowDetails={(_id) => addToast('任务详情功能开发中', 'info')}
          />
        ))}
      </div>
    </div>
  );
}
