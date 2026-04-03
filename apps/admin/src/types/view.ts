export type ViewId = 'view-overview' | 'view-tasks' | 'view-data' | 'view-config' | 'view-log';

export interface ViewConfig {
  id: ViewId;
  title: string;
  subtitle: string;
  navId: string;
}

export const VIEW_CONFIGS: Record<ViewId, ViewConfig> = {
  'view-overview': { id: 'view-overview', title: '数据概览', subtitle: '实时监控 · 自动刷新每 30 秒', navId: 'nav-overview' },
  'view-tasks':    { id: 'view-tasks',    title: '任务调度中心', subtitle: '管理所有后台数据抓取与处理任务', navId: 'nav-tasks' },
  'view-data':     { id: 'view-data',     title: '数据管理', subtitle: '浏览、编辑、导出系统数据库记录', navId: 'nav-data' },
  'view-config':   { id: 'view-config',   title: '系统参数配置', subtitle: '外部接口凭证与全局行为开关', navId: 'nav-config' },
  'view-log':      { id: 'view-log',      title: '操作日志', subtitle: '完整的系统事件与操作记录流', navId: 'nav-log' },
};
