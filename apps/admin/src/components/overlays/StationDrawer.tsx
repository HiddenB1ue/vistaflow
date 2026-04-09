
import { useEffect, useState } from 'react';
import type { AdminStationGeoUpdatePayload, AdminStationRecord } from '@/types/data';
import {
  Button,
  CustomSelect,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
} from '@vistaflow/ui';
import { COMMON_LABELS, STATION_DRAWER_LABELS } from '@/constants/labels';

interface StationDrawerProps {
  isOpen: boolean;
  station: AdminStationRecord | null;
  saving?: boolean;
  onClose: () => void;
  onSave: (payload: AdminStationGeoUpdatePayload) => void;
}

const dataSourceOptions = [
  { value: 'amap', label: STATION_DRAWER_LABELS.dataSources.amap },
  { value: 'manual', label: STATION_DRAWER_LABELS.dataSources.manual },
  { value: 'scraped', label: STATION_DRAWER_LABELS.dataSources.scraped },
];

function formatCoordinateInput(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(6) : '';
}

export function StationDrawer({ isOpen, station, saving = false, onClose, onSave }: StationDrawerProps) {
  const [lng, setLng] = useState('');
  const [lat, setLat] = useState('');
  const [dataSource, setDataSource] = useState('amap');

  useEffect(() => {
    if (station) {
      setLng(formatCoordinateInput(station.longitude));
      setLat(formatCoordinateInput(station.latitude));
      setDataSource(station.geoSource ?? 'manual');
      return;
    }

    setLng('');
    setLat('');
    setDataSource('manual');
  }, [station]);

  const handleSave = () => {
    if (!station) return;

    const normalizedLng = lng.trim();
    const normalizedLat = lat.trim();
    onSave({
      longitude: normalizedLng.length === 0 ? null : Number(normalizedLng),
      latitude: normalizedLat.length === 0 ? null : Number(normalizedLat),
      geoSource: dataSource as AdminStationGeoUpdatePayload['geoSource'],
    });
  };

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={STATION_DRAWER_LABELS.eyebrow}
        title={STATION_DRAWER_LABELS.title}
        subtitle={STATION_DRAWER_LABELS.subtitle(station?.name)}
        onClose={onClose}
        closeLabel="关闭站点详情"
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.name}</label>
              <div className="vf-drawer-meta mt-2">{station?.name ?? '--'}</div>
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.telecode}</label>
              <div className="vf-drawer-meta mt-2 font-mono">{station?.telecode ?? '--'}</div>
            </div>
          </div>
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.pinyin}</label>
              <div className="vf-drawer-meta mt-2">{station?.pinyin ?? '--'}</div>
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.abbr}</label>
              <div className="vf-drawer-meta mt-2">{station?.abbr ?? '--'}</div>
            </div>
          </div>
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.areaName}</label>
              <div className="vf-drawer-meta mt-2">{station?.areaName ?? '--'}</div>
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.countryName}</label>
              <div className="vf-drawer-meta mt-2">{station?.countryName ?? '--'}</div>
            </div>
          </div>
        </section>

        <section className="vf-drawer-group">
          <div>
            <label className="vf-drawer-label">{STATION_DRAWER_LABELS.dataSource}</label>
            <CustomSelect options={dataSourceOptions} value={dataSource} onChange={setDataSource} className="w-full" />
          </div>
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.longitude}</label>
              <InputBox className="w-full font-mono text-[#4ADE80]" value={lng} onChange={(event) => setLng(event.target.value)} />
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.latitude}</label>
              <InputBox className="w-full font-mono text-[#4ADE80]" value={lat} onChange={(event) => setLat(event.target.value)} />
            </div>
          </div>
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.geoUpdatedAt}</label>
              <div className="vf-drawer-meta mt-2">{station?.geoUpdatedAt ?? '--'}</div>
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.updatedAt}</label>
              <div className="vf-drawer-meta mt-2">{station?.updatedAt ?? '--'}</div>
            </div>
          </div>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>{COMMON_LABELS.cancel}</Button>
        <Button variant="primary" onClick={handleSave} disabled={saving}>{saving ? '保存中...' : COMMON_LABELS.save}</Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
