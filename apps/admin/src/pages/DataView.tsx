
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DATA_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import { fetchStations } from '@/services/stationService';
import { useDrawerStore } from '@/stores/drawerStore';
import { useToastStore } from '@/stores/toastStore';
import {
  Button,
  ContentSection,
  ControlToolbar,
  ControlToolbarActions,
  ControlToolbarMain,
  CustomSelect,
  DataTable,
  InputBox,
  PanelBody,
  PanelCard,
  SegmentedControl,
} from '@vistaflow/ui';
import { buildStationColumns, DATA_TABS, stationRowClassName, STATUS_OPTIONS, type DataTab } from './dataView.config';

export default function DataView() {
  const openStationDrawer = useDrawerStore((state) => state.openStationDrawer);
  const addToast = useToastStore((state) => state.addToast);
  const { data: stations = [] } = useQuery({
    queryKey: ['admin', 'stations'],
    queryFn: fetchStations,
  });

  const [activeTab, setActiveTab] = useState<DataTab>('stations');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredStations = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return stations.filter((station) => {
      const matchesKeyword = keyword.length === 0 || [station.name, station.code, station.city].some((field) => field.toLowerCase().includes(keyword));
      const matchesStatus = statusFilter === 'all' || station.coordinateStatus === statusFilter;
      return matchesKeyword && matchesStatus;
    });
  }, [search, stations, statusFilter]);

  return (
    <div className="vf-page-stack">
      <ContentSection spacing="dense">
        <SegmentedControl value={activeTab} onChange={setActiveTab} options={DATA_TABS.map((tab) => ({ value: tab.id, label: tab.label }))} />
      </ContentSection>

      {activeTab === 'stations' && (
        <ContentSection spacing="dense">
          <ControlToolbar>
            <ControlToolbarMain>
              <InputBox placeholder={DATA_LABELS.searchPlaceholder} className="min-w-0 w-full" value={search} onChange={(event) => setSearch(event.target.value)} />
            </ControlToolbarMain>
            <ControlToolbarActions>
              <CustomSelect options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} className="w-full md:w-[180px]" />
              <Button variant="outline" size="sm" onClick={() => addToast(TOAST_MESSAGES.featureInDev(DATA_LABELS.exportCsv), 'info')}>
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {DATA_LABELS.exportCsv}
              </Button>
              <Button variant="primary" size="sm" onClick={() => addToast(TOAST_MESSAGES.featureInDev(DATA_LABELS.addStation), 'info')}>
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                {DATA_LABELS.addStation}
              </Button>
            </ControlToolbarActions>
          </ControlToolbar>

          <PanelCard className="overflow-hidden p-0">
            <PanelBody className="gap-0">
              <DataTable
                columns={buildStationColumns(openStationDrawer)}
                data={filteredStations}
                selectable
                selectedIds={new Set()}
                onSelectionChange={() => {}}
                getId={(station) => station.id}
                rowClassName={stationRowClassName}
              />
              <div className="flex items-center justify-between border-t border-white/5 px-5 py-4 text-xs text-muted">
                <span>{DATA_LABELS.recordsCount(filteredStations.length)}</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="cursor-not-allowed opacity-40" disabled>{DATA_LABELS.prevPage}</Button>
                  <Button variant="outline" size="sm" onClick={() => addToast(TOAST_MESSAGES.featureInDev(DATA_LABELS.nextPage), 'info')}>{DATA_LABELS.nextPage}</Button>
                </div>
              </div>
            </PanelBody>
          </PanelCard>
        </ContentSection>
      )}

      {activeTab === 'routes' && (
        <PanelCard className="items-center justify-center py-12 text-center">
          <PanelBody className="items-center text-center">
            <svg className="mb-4 h-12 w-12 text-muted/30" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <div className="text-sm font-display text-muted">{DATA_LABELS.routeModuleTitle}</div>
            <div className="mt-2 text-xs text-muted/50">{DATA_LABELS.routeModuleDesc}</div>
          </PanelBody>
        </PanelCard>
      )}

      {activeTab === 'price' && (
        <PanelCard className="items-center justify-center py-12 text-center">
          <PanelBody className="items-center text-center">
            <svg className="mb-4 h-12 w-12 text-muted/30" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm font-display text-muted">{DATA_LABELS.priceModuleTitle}</div>
            <div className="mt-2 text-xs text-muted/50">{DATA_LABELS.priceModuleDesc}</div>
            <Button variant="outline" size="sm" className="mt-6" onClick={() => addToast(TOAST_MESSAGES.featureInDev(DATA_LABELS.goConfig), 'info')}>
              {DATA_LABELS.goConfig}
            </Button>
          </PanelBody>
        </PanelCard>
      )}
    </div>
  );
}
