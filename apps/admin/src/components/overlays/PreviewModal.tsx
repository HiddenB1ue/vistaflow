
import { useMemo, useState } from 'react';
import type { StationPreview } from '@/types/station';
import { MOCK_STATION_PREVIEWS } from '@/services/mock/stations.mock';
import { COMMON_LABELS, PREVIEW_LABELS } from '@/constants/labels';
import {
  Badge,
  Button,
  CustomSelect,
  DataTable,
  InputBox,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalShell,
} from '@vistaflow/ui';

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedIds: string[]) => void;
}

const filterOptions = [
  { value: 'success', label: PREVIEW_LABELS.successOnly },
  { value: 'fail', label: PREVIEW_LABELS.failedOnly },
  { value: 'all', label: PREVIEW_LABELS.all },
];

const columns = [
  {
    key: 'name',
    header: '站点名称',
    render: (station: StationPreview) => <span className={`font-medium ${station.failed ? 'text-red-300' : 'text-white'}`}>{station.name}</span>,
  },
  {
    key: 'code',
    header: '站点编码',
    render: (station: StationPreview) => <span className="font-mono text-xs text-muted">{station.code}</span>,
  },
  {
    key: 'lng',
    header: '预解析经度',
    render: (station: StationPreview) => <span className={`font-mono ${station.failed ? 'text-red-400' : station.confidence !== null && station.confidence < 80 ? 'text-[#FACC15]' : 'text-[#4ADE80]'}`}>{station.longitude.toFixed(6)}</span>,
  },
  {
    key: 'lat',
    header: '预解析纬度',
    render: (station: StationPreview) => <span className={`font-mono ${station.failed ? 'text-red-400' : station.confidence !== null && station.confidence < 80 ? 'text-[#FACC15]' : 'text-[#4ADE80]'}`}>{station.latitude.toFixed(6)}</span>,
  },
  {
    key: 'confidence',
    header: '置信度',
    render: (station: StationPreview) => {
      if (station.failed) return <Badge variant="red">{PREVIEW_LABELS.failedBadge}</Badge>;
      if (station.confidence !== null && station.confidence < 80) return <Badge variant="yellow">{station.confidence}%</Badge>;
      return <Badge variant="green">{station.confidence}%</Badge>;
    },
  },
];

export function PreviewModal({ isOpen, onClose, onConfirm }: PreviewModalProps) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('success');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set(MOCK_STATION_PREVIEWS.filter((station) => !station.failed).map((station) => station.id)));

  const filteredPreviews = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return MOCK_STATION_PREVIEWS.filter((item) => {
      const matchesKeyword = keyword.length === 0 || [item.name, item.code].some((field) => field.toLowerCase().includes(keyword));
      const matchesFilter = filter === 'all' ? true : filter === 'success' ? !item.failed : item.failed;
      return matchesKeyword && matchesFilter;
    });
  }, [filter, search]);

  const selectedNonFailed = MOCK_STATION_PREVIEWS.filter((station) => selectedIds.has(station.id) && !station.failed).length;
  const failedCount = MOCK_STATION_PREVIEWS.filter((station) => station.failed).length;

  return (
    <ModalShell open={isOpen} size="xl" onBackdropClick={onClose}>
      <ModalHeader
        eyebrow={PREVIEW_LABELS.eyebrow}
        title={PREVIEW_LABELS.title}
        subtitle={PREVIEW_LABELS.subtitle}
        onClose={onClose}
        closeLabel="关闭预览确认"
      />

      <ModalBody className="gap-5 p-0">
        <div className="flex shrink-0 gap-3 border-b border-white/5 bg-black/20 px-8 py-5">
          <InputBox placeholder={PREVIEW_LABELS.searchPlaceholder} className="flex-1 text-sm" value={search} onChange={(event) => setSearch(event.target.value)} />
          <CustomSelect options={filterOptions} value={filter} onChange={setFilter} className="w-[200px]" />
        </div>

        <div className="flex-1 overflow-y-auto px-8 pb-8" style={{ scrollbarWidth: 'thin' }}>
          <DataTable
            columns={columns}
            data={filteredPreviews}
            selectable
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            getId={(station) => station.id}
            rowClassName={(station) => (station.failed ? 'bg-red-500/5' : '')}
          />
        </div>
      </ModalBody>

      <ModalFooter align="between">
        <div className="text-sm text-muted">{PREVIEW_LABELS.selectedSummary(selectedNonFailed, failedCount)}</div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={onClose}>{COMMON_LABELS.cancel}</Button>
          <Button variant="primary" onClick={() => onConfirm(Array.from(selectedIds))}>{PREVIEW_LABELS.confirm}</Button>
        </div>
      </ModalFooter>
    </ModalShell>
  );
}
