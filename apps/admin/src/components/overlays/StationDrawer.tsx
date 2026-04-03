import { useState, useEffect } from 'react';
import type { Station } from '@/types/station';
import { InputBox, CustomSelect, ProgressBar, Button } from '@vistaflow/ui';

interface StationDrawerProps {
  isOpen: boolean;
  station: Station | null;
  onClose: () => void;
  onSave: (station: Station) => void;
  onDelete: (stationId: string) => void;
}

const dataSourceOptions = [
  { value: 'amap', label: '高德地图 API' },
  { value: 'manual', label: '人工录入' },
  { value: 'scraped', label: '爬虫抓取' },
];

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
      setLng(station.longitude.toFixed(6));
      setLat(station.latitude.toFixed(6));
      setDataSource(station.dataSource);
      setNotes(station.notes ?? '');
    }
  }, [station]);

  const confidence = station?.confidence ?? 98;

  return (
    <div className={`side-drawer ${isOpen ? 'open' : ''}`}>
      <div className="flex justify-between items-center mb-10">
        <div>
          <div className="text-[10px] text-[#8B5CF6] font-display tracking-[0.3em] uppercase mb-2">Station Edit</div>
          <h3 className="font-serif text-3xl italic">编辑站点：{station?.name ?? ''}</h3>
        </div>
        <button className="text-muted hover:text-white p-2 cursor-pointer transition-colors" onClick={onClose}>
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-6 flex-1 overflow-y-auto pr-2" style={{ scrollbarWidth: 'none' }}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">站点名称</label>
            <InputBox className="w-full" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">站点编码</label>
            <InputBox className="w-full font-mono" value={code} onChange={(e) => setCode(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">所属城市</label>
          <InputBox className="w-full" value={city} onChange={(e) => setCity(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">经度 (Lng)</label>
            <InputBox className="w-full font-mono text-[#4ADE80]" value={lng} onChange={(e) => setLng(e.target.value)} />
          </div>
          <div>
            <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">纬度 (Lat)</label>
            <InputBox className="w-full font-mono text-[#4ADE80]" value={lat} onChange={(e) => setLat(e.target.value)} />
          </div>
        </div>
        <div className="glass-panel p-4">
          <div className="text-[10px] text-muted tracking-widest uppercase mb-3">经纬度置信度</div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <ProgressBar value={confidence} color="#4ADE80" />
            </div>
            <span className="text-sm text-[#4ADE80] font-display">{confidence}%</span>
          </div>
          <div className="text-xs text-muted mt-2">来源：高德地图 API · 2026-03-28 自动解析</div>
        </div>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">数据来源标记</label>
          <CustomSelect options={dataSourceOptions} value={dataSource} onChange={setDataSource} className="w-full" />
        </div>
        <div className="border-t border-white/8 pt-6">
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">备注</label>
          <textarea
            className="input-box w-full h-24 resize-none leading-relaxed"
            placeholder="添加备注…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
      </div>

      <div className="pt-7 border-t border-white/8 mt-auto flex gap-4">
        <Button variant="danger" className="flex-1 py-3" size="sm" onClick={() => station && onDelete(station.id)}>删除</Button>
        <Button variant="outline" className="flex-1 py-3" onClick={onClose}>取消</Button>
        <Button variant="primary" className="flex-1 py-3" onClick={() => station && onSave(station)}>保存</Button>
      </div>
    </div>
  );
}
