import { useState } from 'react';
import type { Station } from '@/types/station';
import type { ToastType } from '@/stores/uiStore';
import { MOCK_STATIONS } from '@/services/mock/stations.mock';
import { InputBox, CustomSelect, Button, Badge, DataTable } from '@vistaflow/ui';

interface DataViewProps {
  onEditStation: (station: Station) => void;
  addToast: (message: string, type: ToastType) => void;
}

type DataTab = 'stations' | 'routes' | 'price';

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'ok', label: '坐标完整' },
  { value: 'missing', label: '坐标缺失' },
];

const coordColorMap: Record<string, string> = {
  complete: 'text-[#4ADE80]',
  'low-confidence': 'text-[#FACC15]',
  missing: 'text-red-400',
};

const statusBadgeMap: Record<string, { variant: 'green' | 'yellow' | 'red'; label: string }> = {
  complete: { variant: 'green', label: '完整' },
  'low-confidence': { variant: 'yellow', label: '低置信度' },
  missing: { variant: 'red', label: '缺失' },
};

const columns = (onEdit: (station: Station) => void) => [
  { key: 'name', header: '站点名称', render: (s: Station) => <span className={`font-medium ${s.coordinateStatus === 'missing' ? 'text-red-300' : 'text-white'}`}>{s.name}</span> },
  { key: 'code', header: '编码', render: (s: Station) => <span className="font-mono text-muted text-xs">{s.code}</span> },
  { key: 'city', header: '所属城市', render: (s: Station) => s.city },
  { key: 'lng', header: '经度', render: (s: Station) => <span className={`font-mono text-xs ${coordColorMap[s.coordinateStatus] ?? ''}`}>{s.longitude.toFixed(6)}</span> },
  { key: 'lat', header: '纬度', render: (s: Station) => <span className={`font-mono text-xs ${coordColorMap[s.coordinateStatus] ?? ''}`}>{s.latitude.toFixed(6)}</span> },
  { key: 'status', header: '坐标状态', render: (s: Station) => { const b = statusBadgeMap[s.coordinateStatus]; return b ? <Badge variant={b.variant}>{b.label}</Badge> : null; } },
  { key: 'updated', header: '最近更新', render: (s: Station) => <span className="text-xs text-muted">{s.lastUpdated}</span> },
  {
    key: 'action', header: '操作', className: 'text-center',
    render: (s: Station) => {
      if (s.coordinateStatus === 'low-confidence') {
        return <Button variant="warning" size="sm" onClick={() => onEdit(s)}>核实</Button>;
      }
      return <Button variant="outline" size="sm" onClick={() => onEdit(s)}>编辑</Button>;
    },
  },
];

export function DataView({ onEditStation, addToast }: DataViewProps) {
  const [activeTab, setActiveTab] = useState<DataTab>('stations');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const tabs: { id: DataTab; label: string }[] = [
    { id: 'stations', label: '车站数据' },
    { id: 'routes', label: '线路数据' },
    { id: 'price', label: '票价矩阵' },
  ];

  const rowClassName = (s: Station) => {
    if (s.coordinateStatus === 'low-confidence') return 'bg-[#FACC15]/[0.03]';
    if (s.coordinateStatus === 'missing') return 'bg-[#F87171]/[0.03]';
    return '';
  };

  return (
    <div>
      {/* Sub-tabs */}
      <div className="flex gap-2 mb-6 bg-white/3 rounded-lg p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Stations tab */}
      {activeTab === 'stations' && (
        <div>
          <div className="flex flex-wrap gap-3 mb-5">
            <InputBox placeholder="搜索站点名称或编码…" className="flex-1 min-w-48" value={search} onChange={(e) => setSearch(e.target.value)} />
            <CustomSelect options={statusOptions} value={statusFilter} onChange={setStatusFilter} className="w-[155px]" />
            <Button variant="outline" size="sm" onClick={() => addToast('导出功能开发中', 'info')}>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              导出 CSV
            </Button>
            <Button variant="primary" size="sm" onClick={() => addToast('手动录入功能开发中', 'info')}>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              新增站点
            </Button>
          </div>

          <div className="glass-panel overflow-hidden">
            <DataTable
              columns={columns(onEditStation)}
              data={MOCK_STATIONS}
              selectable
              selectedIds={new Set()}
              onSelectionChange={() => {}}
              getId={(s) => s.id}
              rowClassName={rowClassName}
            />
            <div className="px-5 py-4 border-t border-white/5 flex justify-between items-center text-xs text-muted">
              <span>共 3,412 条 · 显示第 1–5 条</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="opacity-40 cursor-not-allowed" disabled>← 上一页</Button>
                <Button variant="outline" size="sm" onClick={() => addToast('翻页功能开发中', 'info')}>下一页 →</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Routes placeholder */}
      {activeTab === 'routes' && (
        <div className="glass-panel p-12 flex flex-col items-center justify-center text-center">
          <svg className="w-12 h-12 text-muted/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <div className="text-muted text-sm font-display">线路数据模块</div>
          <div className="text-muted/50 text-xs mt-2">开发中，预计下个版本上线</div>
        </div>
      )}

      {/* Price placeholder */}
      {activeTab === 'price' && (
        <div className="glass-panel p-12 flex flex-col items-center justify-center text-center">
          <svg className="w-12 h-12 text-muted/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-muted text-sm font-display">票价矩阵模块</div>
          <div className="text-muted/50 text-xs mt-2">需先完成代理凭证配置</div>
          <Button variant="outline" size="sm" className="mt-6" onClick={() => addToast('前往配置页面', 'info')}>前往配置</Button>
        </div>
      )}
    </div>
  );
}
