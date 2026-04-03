import { useState } from 'react';
import { InputBox, CustomSelect, ToggleSwitch, Button } from '@vistaflow/ui';

interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

const taskTypeOptions = [
  { value: 'fetch-status', label: '车次实时状态同步' },
  { value: 'fetch-station', label: '基础车站静态抓取' },
  { value: 'geocode', label: '站点经纬度补全' },
  { value: 'price', label: '票价矩阵更新' },
  { value: 'cleanup', label: '过期数据清理' },
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
    onSubmit(taskName.trim() || '新任务');
    setTaskName('');
  };

  return (
    <div className={`side-drawer ${isOpen ? 'open' : ''}`}>
      <div className="flex justify-between items-center mb-10">
        <div>
          <div className="text-[10px] text-[#8B5CF6] font-display tracking-[0.3em] uppercase mb-2">New Task</div>
          <h3 className="font-serif text-3xl italic">配置调度任务</h3>
        </div>
        <button className="text-muted hover:text-white p-2 cursor-pointer transition-colors" onClick={onClose}>
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-7 flex-1 overflow-y-auto pr-2" style={{ scrollbarWidth: 'none' }}>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">任务名称</label>
          <InputBox className="w-full" placeholder="例如：核心线路票源同步" value={taskName} onChange={(e) => setTaskName(e.target.value)} />
        </div>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">任务类型</label>
          <CustomSelect options={taskTypeOptions} value={taskType} onChange={setTaskType} className="w-full" />
        </div>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">目标日期偏移</label>
          <InputBox className="w-full" placeholder="例如：T+0 至 T+30" value={dateOffset} onChange={(e) => setDateOffset(e.target.value)} />
        </div>
        <div className="border-t border-white/8 pt-7">
          <div className="flex items-center justify-between mb-5">
            <span className="text-sm text-starlight">定时自动执行</span>
            <ToggleSwitch checked={cronEnabled} onChange={setCronEnabled} />
          </div>
          <div className={cronEnabled ? '' : 'opacity-30'}>
            <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">Cron 表达式</label>
            <InputBox className="w-full font-mono text-sm text-[#8B5CF6]" value={cronExpr} onChange={(e) => setCronExpr(e.target.value)} placeholder="* * * * * *" />
            <div className="mt-3 text-xs text-muted/60 leading-relaxed">
              每 15 分钟执行一次。下次执行于 <span className="text-[#8B5CF6]">12:15</span>
            </div>
          </div>
        </div>
        <div>
          <label className="block text-[10px] text-muted tracking-widest uppercase mb-3">失败重试</label>
          <div className="flex items-center gap-3">
            <input type="number" className="input-box w-24 text-center" value={retryCount} onChange={(e) => setRetryCount(e.target.value)} min={0} max={10} />
            <span className="text-sm text-muted">次，间隔</span>
            <input type="number" className="input-box w-24 text-center" value={retryInterval} onChange={(e) => setRetryInterval(e.target.value)} min={0} />
            <span className="text-sm text-muted">秒</span>
          </div>
        </div>
      </div>

      <div className="pt-7 border-t border-white/8 mt-auto flex gap-4">
        <Button variant="outline" className="flex-1 py-4" onClick={onClose}>取消</Button>
        <Button variant="primary" className="flex-1 py-4" onClick={handleSubmit}>部署任务</Button>
      </div>
    </div>
  );
}
