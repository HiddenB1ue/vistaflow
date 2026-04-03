import { ToggleSwitch } from '@vistaflow/ui';

interface FilterDrawerProps {
  isOpen: boolean;
  directOnly: boolean;
  business: boolean;
  first: boolean;
  second: boolean;
  onDirectOnlyChange: (v: boolean) => void;
  onBusinessChange: (v: boolean) => void;
  onFirstChange: (v: boolean) => void;
  onSecondChange: (v: boolean) => void;
  onClose: () => void;
}

export function FilterDrawer({
  isOpen,
  directOnly,
  business,
  first,
  second,
  onDirectOnlyChange,
  onBusinessChange,
  onFirstChange,
  onSecondChange,
  onClose,
}: FilterDrawerProps) {
  return (
    <div id="filter-drawer" className={isOpen ? 'open' : ''}>
      {/* 标题 */}
      <div className="flex justify-between items-center mb-16">
        <div>
          <div className="text-xs time-theme-text font-display tracking-[0.3em] uppercase mb-2">
            Preferences
          </div>
          <h3 className="font-serif text-3xl italic text-starlight">
            出行偏好
          </h3>
        </div>
        <button
          aria-label="关闭偏好设置"
          className="cursor-pointer p-2 text-muted hover:text-white transition-colors"
          onClick={onClose}
        >
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* 选项区 */}
      <div className="space-y-12 flex-1 overflow-y-auto pr-4" style={{ scrollbarWidth: 'none' }}>
        {/* 仅看直达 */}
        <div>
          <div className="text-sm text-starlight mb-6 flex items-center justify-between">
            <span>仅看直达</span>
            <ToggleSwitch
              checked={directOnly}
              onChange={onDirectOnlyChange}
            />
          </div>
          <p className="text-xs text-muted font-light leading-relaxed">
            只显示无需换乘的直达车次。
          </p>
        </div>

        {/* 座位偏好 */}
        <div className="border-t border-white/10 pt-10">
          <div className="text-xs text-muted tracking-widest uppercase mb-6">
            座位偏好
          </div>
          <div className="space-y-6 text-sm text-starlight">
            {([
              { label: '商务座 / 特等座', value: business, onChange: onBusinessChange },
              { label: '一等座', value: first, onChange: onFirstChange },
              { label: '二等座', value: second, onChange: onSecondChange },
            ] as const).map(({ label, value, onChange }) => (
              <div key={label} className="flex items-center justify-between">
                <span>{label}</span>
                <ToggleSwitch checked={value} onChange={onChange} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 保存按钮 */}
      <div className="pt-8 border-t border-white/10 mt-auto">
        <button
          className="w-full py-5 rounded-lg text-sm font-medium tracking-[0.2em] uppercase cursor-pointer hover-time-theme transition-colors bg-starlight text-void"
          onClick={onClose}
        >
          保存设置
        </button>
      </div>
    </div>
  );
}
