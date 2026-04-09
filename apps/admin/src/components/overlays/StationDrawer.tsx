
import { useEffect, useState } from 'react';
import type { Station } from '@/types/station';
import {
  Button,
  CustomSelect,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
  PanelCard,
  ProgressBar,
  Textarea,
} from '@vistaflow/ui';
import { COMMON_LABELS, STATION_DRAWER_LABELS } from '@/constants/labels';

interface StationDrawerProps {
  isOpen: boolean;
  station: Station | null;
  onClose: () => void;
  onSave: (station: Station) => void;
  onDelete: (stationId: string) => void;
}

const dataSourceOptions = [
  { value: 'amap', label: STATION_DRAWER_LABELS.dataSources.amap },
  { value: 'manual', label: STATION_DRAWER_LABELS.dataSources.manual },
  { value: 'scraped', label: STATION_DRAWER_LABELS.dataSources.scraped },
];

function formatCoordinateInput(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(6) : '';
}

export function StationDrawer({ isOpen, station, onClose, onSave, onDelete }: StationDrawerProps) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [city, setCity] = useState('');
  const [lng, setLng] = useState('');
  const [lat, setLat] = useState('');
  const [dataSource, setDataSource] = useState('amap');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (station) {
      setName(station.name);
      setCode(station.code);
      setCity(station.city);
      setLng(formatCoordinateInput(station.longitude));
      setLat(formatCoordinateInput(station.latitude));
      setDataSource(station.dataSource);
      setNotes(station.notes ?? '');
      return;
    }

    setName('');
    setCode('');
    setCity('');
    setLng('');
    setLat('');
    setDataSource('amap');
    setNotes('');
  }, [station]);

  const confidence = station?.confidence ?? 98;

  const handleSave = () => {
    if (!station) return;

    onSave({
      ...station,
      name,
      code,
      city,
      longitude: Number(lng) || station.longitude,
      latitude: Number(lat) || station.latitude,
      dataSource: dataSource as Station['dataSource'],
      notes,
    });
  };

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={STATION_DRAWER_LABELS.eyebrow}
        title={STATION_DRAWER_LABELS.title}
        subtitle={STATION_DRAWER_LABELS.subtitle(station?.name)}
        onClose={onClose}
        closeLabel="关闭站点编辑"
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div className="vf-drawer-grid-2">
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.name}</label>
              <InputBox className="w-full" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div>
              <label className="vf-drawer-label">{STATION_DRAWER_LABELS.code}</label>
              <InputBox className="w-full font-mono" value={code} onChange={(event) => setCode(event.target.value)} />
            </div>
          </div>
          <div>
            <label className="vf-drawer-label">{STATION_DRAWER_LABELS.city}</label>
            <InputBox className="w-full" value={city} onChange={(event) => setCity(event.target.value)} />
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
        </section>

        <section className="vf-drawer-group">
          <PanelCard className="gap-3">
            <div className="vf-drawer-label mb-3">{STATION_DRAWER_LABELS.confidence}</div>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <ProgressBar value={confidence} color="#4ADE80" />
              </div>
              <span className="font-display text-sm text-[#4ADE80]">{confidence}%</span>
            </div>
            <div className="vf-drawer-meta mt-3">{STATION_DRAWER_LABELS.confidenceSource}</div>
          </PanelCard>

          <div>
            <label className="vf-drawer-label">{STATION_DRAWER_LABELS.dataSource}</label>
            <CustomSelect options={dataSourceOptions} value={dataSource} onChange={setDataSource} className="w-full" />
          </div>
        </section>

        <section className="vf-drawer-group">
          <div>
            <label className="vf-drawer-label">{STATION_DRAWER_LABELS.notes}</label>
            <Textarea className="h-24 w-full resize-none leading-relaxed" placeholder={STATION_DRAWER_LABELS.notesPlaceholder} value={notes} onChange={(event) => setNotes(event.target.value)} />
          </div>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="danger" size="sm" onClick={() => station && onDelete(station.id)}>{COMMON_LABELS.delete}</Button>
        <Button variant="outline" onClick={onClose}>{COMMON_LABELS.cancel}</Button>
        <Button variant="primary" onClick={handleSave}>{COMMON_LABELS.save}</Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
