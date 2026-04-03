import { useState } from 'react';
import type { StationPreview } from '@/types/station';
import { MOCK_STATION_PREVIEWS } from '@/services/mock/stations.mock';
import { InputBox } from '@/components/ui/InputBox';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { Badge } from '@/components/ui/Badge';
import { DataTable } from '@/components/ui/DataTable';
import { Button } from '@/components/ui/Button';

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedIds: string[]) => void;
}

const filterOptions = [
  { value: 'success', label: '解析成功项' },
  { value: 'fail', label: '解析失败项' },
  { value: 'all', label: '全部' },
];

const columns = [
  {
    key: 'name', header: '站点名称',
    render: (s: StationPreview) => <span className={`font-medium ${s.failed ? 'text-red-300' : 'text-white'}`}>{s.name}</span>,
  },
  {
    key: 'code', header: '站点编码',
    render: (s: StationPreview) => <span className="font-mono text-muted text-xs">{s.code}</span>,
  },
  {
    key: 'lng', header: '预解析经度',
    render: (s: StationPreview) => <span className={`font-mono ${s.failed ? 'text-red-400' : s.confidence !== null && s.confidence < 80 ? 'text-[#FACC15]' : 'text-[#4ADE80]'}`}>{s.longitude.toFixed(6)}</span>,
  },
  {
    key: 'lat', header: '预解析纬度',
    render: (s: StationPreview) => <span className={`font-mono ${s.failed ? 'text-red-400' : s.confidence !== null && s.confidence < 80 ? 'text-[#FACC15]' : 'text-[#4ADE80]'}`}>{s.latitude.toFixed(6)}</span>,
  },
  {
    key: 'confidence', header: '置信度',
    render: (s: StationPreview) => {
      if (s.failed) return <Badge variant="red">Failed</Badge>;
      if (s.confidence !== null && s.confidence < 80) return <Badge variant="yellow">{s.confidence}%</Badge>;
      return <Badge variant="green">{s.confidence}%</Badge>;
    },
  },
];

export function PreviewModal({ isOpen, onClose, onConfirm }: PreviewModalProps) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('success');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => {
    return new Set(MOCK_STATION_PREVIEWS.filter((s) => !s.failed).map((s) => s.id));
  });

  const selectedNonFailed = MOCK_STATION_PREVIEWS.filter((s) => selectedIds.has(s.id) && !s.failed).length;
  const failedCount = MOCK_STATION_PREVIEWS.filter((s) => s.failed).length;

  const handleConfirm = () => {
    onConfirm(Array.from(selectedIds));
  };

  return (
    <div className={`modal-overlay ${isOpen ? 'show' : ''}`} style={{ display: isOpen ? 'flex' : 'none' }}>
      <div className="modal-box w-11/12 max-w-5xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-white/8 flex justify-between items-center bg-white/3 rounded-t-[20px]">
          <div>
            <div className="text-[10px] text-[#FACC15] tracking-[0.2em] uppercase mb-1">Manual Action Required</div>
            <h2 className="font-serif text-2xl text-white">经纬度补全 · 数据预览与确认</h2>
          </div>
          <button onClick={onClose} className="text-muted hover:text-white p-2 cursor-pointer transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filter bar */}
        <div className="p-5 flex gap-3 border-b border-white/5 bg-black/20 shrink-0">
          <InputBox placeholder="搜索站点名称…" className="flex-1 text-sm" value={search} onChange={(e) => setSearch(e.target.value)} />
          <CustomSelect options={filterOptions} value={filter} onChange={setFilter} className="w-[200px]" />
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
          <DataTable
            columns={columns}
            data={MOCK_STATION_PREVIEWS}
            selectable
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            getId={(s) => s.id}
            rowClassName={(s) => s.failed ? 'bg-red-500/5' : ''}
          />
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-white/8 flex justify-between items-center bg-black/20 rounded-b-[20px]">
          <div className="text-sm text-muted">
            已选 <span className="text-white font-bold">{selectedNonFailed}</span> 项 · {failedCount} 项失败已跳过
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose}>取消</Button>
            <Button variant="primary" onClick={handleConfirm}>确认并落库</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
