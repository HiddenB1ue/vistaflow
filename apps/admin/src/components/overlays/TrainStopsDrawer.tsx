import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AdminTrainRecord } from '@/types/data';
import { fetchAdminTrainStops } from '@/services/adminDataService';
import { COMMON_LABELS, DATA_LABELS, TRAIN_DRAWER_LABELS } from '@/constants/labels';
import {
  Button,
  DataTable,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  PanelCard,
} from '@vistaflow/ui';
import { buildTrainStopColumns } from '@/pages/dataView.config';

interface TrainStopsDrawerProps {
  isOpen: boolean;
  train: AdminTrainRecord | null;
  onClose: () => void;
}

export function TrainStopsDrawer({ isOpen, train, onClose }: TrainStopsDrawerProps) {
  const { data: stops = [], isLoading } = useQuery({
    queryKey: ['admin', 'data', 'train-stops', train?.id],
    queryFn: () => fetchAdminTrainStops(train!.id),
    enabled: isOpen && train !== null,
  });

  const columns = useMemo(() => buildTrainStopColumns(), []);

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={TRAIN_DRAWER_LABELS.eyebrow}
        title={TRAIN_DRAWER_LABELS.title}
        subtitle={TRAIN_DRAWER_LABELS.subtitle(train?.stationTrainCode ?? train?.trainNo)}
        onClose={onClose}
        closeLabel={COMMON_LABELS.close}
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <PanelCard className="gap-4">
            <div className="vf-drawer-grid-2">
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.trainNo}</div>
                <div className="vf-drawer-meta mt-2 font-mono">{train?.trainNo ?? DATA_LABELS.unknown}</div>
              </div>
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.stationTrainCode}</div>
                <div className="vf-drawer-meta mt-2">{train?.stationTrainCode ?? DATA_LABELS.unknown}</div>
              </div>
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.fromStation}</div>
                <div className="vf-drawer-meta mt-2">{train?.fromStation ?? DATA_LABELS.unknown}</div>
              </div>
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.toStation}</div>
                <div className="vf-drawer-meta mt-2">{train?.toStation ?? DATA_LABELS.unknown}</div>
              </div>
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.totalNum}</div>
                <div className="vf-drawer-meta mt-2">{typeof train?.totalNum === 'number' ? train.totalNum : DATA_LABELS.unknown}</div>
              </div>
              <div>
                <div className="vf-drawer-label">{TRAIN_DRAWER_LABELS.updatedAt}</div>
                <div className="vf-drawer-meta mt-2">{train?.updatedAt ?? DATA_LABELS.unknown}</div>
              </div>
            </div>
          </PanelCard>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label mb-3">{TRAIN_DRAWER_LABELS.title}</div>
          {isLoading ? (
            <div className="vf-drawer-meta">{TRAIN_DRAWER_LABELS.loading}</div>
          ) : stops.length === 0 ? (
            <div className="vf-drawer-meta">{DATA_LABELS.noStops}</div>
          ) : (
            <PanelCard className="overflow-hidden p-0">
              <div className="overflow-x-auto">
                <div className="min-w-[980px]">
                  <DataTable
                    columns={columns}
                    data={stops}
                    getId={(stop) => String(stop.stationNo)}
                  />
                </div>
              </div>
            </PanelCard>
          )}
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>{COMMON_LABELS.close}</Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
