
import { useState } from 'react';
import {
  Button,
  CustomSelect,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
  NumberInput,
  ToggleSwitch,
} from '@vistaflow/ui';
import { COMMON_LABELS, TASK_DRAWER_LABELS } from '@/constants/labels';

interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

const taskTypeOptions = [
  { value: 'fetch-status', label: TASK_DRAWER_LABELS.types.fetchStatus },
  { value: 'fetch-station', label: TASK_DRAWER_LABELS.types.fetchStation },
  { value: 'geocode', label: TASK_DRAWER_LABELS.types.geocode },
  { value: 'price', label: TASK_DRAWER_LABELS.types.price },
  { value: 'cleanup', label: TASK_DRAWER_LABELS.types.cleanup },
];

export function TaskDrawer({ isOpen, onClose, onSubmit }: TaskDrawerProps) {
  const [taskName, setTaskName] = useState('');
  const [taskType, setTaskType] = useState('fetch-status');
  const [dateOffset, setDateOffset] = useState('');
  const [cronEnabled, setCronEnabled] = useState(true);
  const [cronExpr, setCronExpr] = useState('0 0/15 * * * ?');
  const [retryCount, setRetryCount] = useState('3');
  const [retryInterval, setRetryInterval] = useState('60');

  const handleSubmit = () => {
    onSubmit(taskName.trim() || TASK_DRAWER_LABELS.defaultTaskName);
    setTaskName('');
  };

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={TASK_DRAWER_LABELS.eyebrow}
        title={TASK_DRAWER_LABELS.title}
        subtitle={TASK_DRAWER_LABELS.subtitle}
        onClose={onClose}
        closeLabel="关闭任务配置"
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.name}</label>
            <InputBox className="w-full" placeholder={TASK_DRAWER_LABELS.namePlaceholder} value={taskName} onChange={(event) => setTaskName(event.target.value)} />
          </div>
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.type}</label>
            <CustomSelect options={taskTypeOptions} value={taskType} onChange={setTaskType} className="w-full" />
          </div>
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.dateOffset}</label>
            <InputBox className="w-full" placeholder={TASK_DRAWER_LABELS.dateOffsetPlaceholder} value={dateOffset} onChange={(event) => setDateOffset(event.target.value)} />
          </div>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-toggle-row">
            <span className="vf-drawer-toggle-row__title">{TASK_DRAWER_LABELS.cronEnabled}</span>
            <ToggleSwitch checked={cronEnabled} onChange={setCronEnabled} />
          </div>
          <div className={cronEnabled ? '' : 'opacity-35'}>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.cronExpr}</label>
            <InputBox
              className="w-full font-mono text-sm text-[#8B5CF6]"
              value={cronExpr}
              onChange={(event) => setCronExpr(event.target.value)}
              placeholder="* * * * * *"
            />
            <div className="vf-drawer-meta mt-3">
              {TASK_DRAWER_LABELS.cronHint}<span className="text-[#8B5CF6]">12:15</span>
            </div>
          </div>
        </section>

        <section className="vf-drawer-group">
          <label className="vf-drawer-label">{TASK_DRAWER_LABELS.retry}</label>
          <div className="flex items-center gap-3">
            <NumberInput className="w-24 text-center" value={retryCount} onChange={(event) => setRetryCount(event.target.value)} min={0} max={10} />
            <span className="text-sm text-muted">{TASK_DRAWER_LABELS.retryTimes}</span>
            <NumberInput className="w-24 text-center" value={retryInterval} onChange={(event) => setRetryInterval(event.target.value)} min={0} />
            <span className="text-sm text-muted">{TASK_DRAWER_LABELS.retrySeconds}</span>
          </div>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>{COMMON_LABELS.cancel}</Button>
        <Button variant="primary" onClick={handleSubmit}>{TASK_DRAWER_LABELS.submit}</Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
