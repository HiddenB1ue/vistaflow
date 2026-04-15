import { useState } from 'react';
import {
  Button,
  ComboboxInput,
  CustomSelect,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
  ToggleSwitch,
} from '@vistaflow/ui';
import { TimeWheelField } from '@/components/inputs/TimeWheelField';
import { fetchStationSuggestions } from '@/services/stationService';
import type { SearchParams, SearchSuggestion } from '@/types/search';

interface SearchFilterDrawerProps {
  isOpen: boolean;
  params: SearchParams;
  onChange: (patch: Partial<SearchParams>) => void;
  onClose: () => void;
}

const transferCountOptions = [
  { value: '0', label: '仅直达' },
  { value: '1', label: '最多 1 次换乘' },
  { value: '2', label: '最多 2 次换乘' },
  { value: '3', label: '最多 3 次换乘' },
];

const minuteOptions = [10, 15, 20, 30, 45, 60, 90, 120, 180].map((value) => ({
  value: String(value),
  label: `${value} 分钟`,
}));

const maxTransferMinuteOptions = [
  { value: '', label: '不限制' },
  ...minuteOptions,
];

const trainTypeOptions = [
  { value: 'G', label: '高铁 G' },
  { value: 'D', label: '动车 D' },
  { value: 'C', label: '城际 C' },
  { value: 'Z', label: '直达特快 Z' },
  { value: 'T', label: '特快 T' },
  { value: 'K', label: '快速 K' },
  { value: 'S', label: '市郊 S' },
  { value: 'Y', label: '旅游 Y' },
  { value: 'L', label: '临客 L' },
];

function addUniqueValue(values: string[], rawValue: string): string[] {
  const value = rawValue.trim();
  if (!value || values.includes(value)) {
    return values;
  }
  return [...values, value];
}

function removeValue(values: string[], value: string): string[] {
  return values.filter((item) => item !== value);
}

function FilterChip({
  value,
  onRemove,
}: {
  value: string;
  onRemove: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onRemove}
      className="rounded-full border border-white/15 px-3 py-1 text-xs tracking-[0.12em] text-starlight transition hover:border-white/40"
    >
      {value} ×
    </button>
  );
}

function TrainTypeToggle({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-2 text-xs tracking-[0.14em] transition ${
        active
          ? 'border-transparent time-theme-bg shadow-[0_6px_18px_var(--color-pulse-shadow)]'
          : 'border-white/10 bg-white/5 text-starlight hover:border-white/25 hover:bg-white/8'
      }`}
      style={active ? { color: 'var(--color-pulse-contrast)' } : undefined}
    >
      {label}
    </button>
  );
}

function TrainNumberField({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [draft, setDraft] = useState('');

  const addTrain = () => {
    const next = addUniqueValue(values, draft.toUpperCase());
    onChange(next);
    setDraft('');
  };

  return (
    <div className="space-y-3">
      <label className="vf-drawer-label">{label}</label>
      <div className="flex items-center gap-3">
        <InputBox
          value={draft}
          placeholder={placeholder}
          onChange={(event) => setDraft(event.target.value.toUpperCase())}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              addTrain();
            }
          }}
        />
        <Button variant="outline" size="sm" onClick={addTrain}>
          添加
        </Button>
      </div>
      {values.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {values.map((value) => (
            <FilterChip
              key={value}
              value={value}
              onRemove={() => onChange(removeValue(values, value))}
            />
          ))}
        </div>
      ) : (
        <p className="vf-drawer-meta">暂未添加任何车次。</p>
      )}
    </div>
  );
}

function StationField({
  label,
  values,
  onChange,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [draft, setDraft] = useState('');

  const addStation = () => {
    const next = addUniqueValue(values, draft);
    onChange(next);
    setDraft('');
  };

  return (
    <div className="space-y-3">
      <label className="vf-drawer-label">{label}</label>
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <ComboboxInput<SearchSuggestion>
            value={draft}
            onValueChange={setDraft}
            loadOptions={fetchStationSuggestions}
            getOptionId={(item) => item.id}
            getOptionLabel={(item) => item.name}
            getOptionDescription={(item) => item.city}
            appearance="boxed"
            placeholder="输入车站名"
            aria-label={label}
            autoSelectOnBlur={true}
            onEnterKey={addStation}
          />
        </div>
        <Button variant="outline" size="sm" onClick={addStation}>
          添加
        </Button>
      </div>
      {values.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {values.map((value) => (
            <FilterChip
              key={value}
              value={value}
              onRemove={() => onChange(removeValue(values, value))}
            />
          ))}
        </div>
      ) : (
        <p className="vf-drawer-meta">暂未添加任何车站。</p>
      )}
    </div>
  );
}

export function SearchFilterDrawer({
  isOpen,
  params,
  onChange,
  onClose,
}: SearchFilterDrawerProps) {
  const toggleTrainType = (
    field: 'allowedTrainTypes' | 'excludedTrainTypes',
    trainType: string,
  ) => {
    const current = params[field];
    const next = current.includes(trainType)
      ? current.filter((item) => item !== trainType)
      : [...current, trainType];
    onChange({ [field]: next } as Pick<SearchParams, typeof field>);
  };

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow="搜索参数"
        title="候选池生成规则"
        subtitle="这里的参数会影响搜索范围，并决定 Redis 中缓存的候选结果。"
        onClose={onClose}
        closeLabel="关闭搜索参数"
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div className="vf-drawer-label">换乘规则</div>
          <div className="space-y-4">
            <div>
              <label className="vf-drawer-label">最多换乘次数</label>
              <CustomSelect
                options={transferCountOptions}
                value={String(params.transferCount)}
                onChange={(value) => onChange({ transferCount: Number(value) })}
              />
            </div>
            <div>
              <label className="vf-drawer-label">最短换乘时间</label>
              <CustomSelect
                options={minuteOptions}
                value={String(params.minTransferMinutes)}
                onChange={(value) => onChange({ minTransferMinutes: Number(value) })}
              />
            </div>
            <div>
              <label className="vf-drawer-label">最长换乘时间</label>
              <CustomSelect
                options={maxTransferMinuteOptions}
                value={params.maxTransferMinutes}
                onChange={(value) => onChange({ maxTransferMinutes: value })}
              />
            </div>
          </div>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">时间约束</div>
          <div className="grid grid-cols-1 gap-4">
            <TimeWheelField
              label="最早出发时间"
              value={params.departureTimeStart}
              onChange={(next) => onChange({ departureTimeStart: next })}
            />
            <TimeWheelField
              label="最晚出发时间"
              value={params.departureTimeEnd}
              onChange={(next) => onChange({ departureTimeEnd: next })}
            />
            <TimeWheelField
              label="最晚到达时间"
              value={params.arrivalDeadline}
              onChange={(next) => onChange({ arrivalDeadline: next })}
            />
          </div>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">允许车次类型</div>
          <div className="flex flex-wrap gap-2">
            {trainTypeOptions.map((option) => (
              <TrainTypeToggle
                key={`allow-${option.value}`}
                active={params.allowedTrainTypes.includes(option.value)}
                label={option.label}
                onClick={() => toggleTrainType('allowedTrainTypes', option.value)}
              />
            ))}
          </div>
          <p className="vf-drawer-meta">仅保留这些车次类型，留空表示不限制。</p>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">排除车次类型</div>
          <div className="flex flex-wrap gap-2">
            {trainTypeOptions.map((option) => (
              <TrainTypeToggle
                key={`exclude-${option.value}`}
                active={params.excludedTrainTypes.includes(option.value)}
                label={option.label}
                onClick={() => toggleTrainType('excludedTrainTypes', option.value)}
              />
            ))}
          </div>
          <p className="vf-drawer-meta">这些车次类型会从候选池里直接排除。</p>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">车次限制</div>
          <div className="space-y-5">
            <TrainNumberField
              label="允许车次"
              placeholder="输入车次，例如 G1、D11"
              values={params.allowedTrains}
              onChange={(values) => onChange({ allowedTrains: values })}
            />
            <TrainNumberField
              label="排除车次"
              placeholder="输入车次，例如 K9、T17"
              values={params.excludedTrains}
              onChange={(values) => onChange({ excludedTrains: values })}
            />
          </div>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">换乘站限制</div>
          <div className="space-y-5">
            <StationField
              label="允许换乘站"
              values={params.allowedTransferStations}
              onChange={(values) => onChange({ allowedTransferStations: values })}
            />
            <StationField
              label="排除换乘站"
              values={params.excludedTransferStations}
              onChange={(values) => onChange({ excludedTransferStations: values })}
            />
          </div>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">附加选项</div>
          <div className="space-y-5 text-sm text-starlight">
            <div className="vf-drawer-toggle-row">
              <span>启用票务补充信息</span>
              <ToggleSwitch
                checked={params.enableTicketEnrich}
                onChange={(value) => onChange({ enableTicketEnrich: value })}
              />
            </div>
          </div>
          <p className="vf-drawer-meta">
            开启后会尽量补充票价和席别等信息，但搜索可能会更慢。
          </p>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="primary" onClick={onClose}>
          应用搜索参数
        </Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
