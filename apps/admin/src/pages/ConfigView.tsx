import { useState } from 'react';
import type { ToastType } from '@/stores/uiStore';
import { MOCK_CREDENTIALS, MOCK_TOGGLES } from '@/services/mock/config.mock';
import { Badge, Button, ToggleSwitch } from '@vistaflow/ui';

interface ConfigViewProps {
  addToast: (message: string, type: ToastType) => void;
}

export function ConfigView({ addToast }: ConfigViewProps) {
  const [testing, setTesting] = useState(false);
  const [toggleStates, setToggleStates] = useState<Record<string, boolean>>(
    Object.fromEntries(MOCK_TOGGLES.map((t) => [t.id, t.enabled])),
  );

  const handleTestConnection = () => {
    setTesting(true);
    setTimeout(() => {
      setTesting(false);
      addToast('接口连通性测试通过 · 延迟 42ms', 'success');
    }, 1600);
  };

  const handleToggle = (id: string, checked: boolean) => {
    setToggleStates((prev) => ({ ...prev, [id]: checked }));
  };

  const healthyCred = MOCK_CREDENTIALS.find((c) => c.health === 'healthy');
  const expiredCred = MOCK_CREDENTIALS.find((c) => c.health === 'expired');

  return (
    <div>
      <p className="text-sm text-muted max-w-2xl leading-relaxed mb-8">
        管理后台运行所依赖的外部参数与凭证。修改后实时生效，请确保密钥有效。点击"连通性检测"验证配置健康度。
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Healthy credential */}
        {healthyCred && (
          <div className="glass-panel p-6 flex flex-col">
            <div className="flex justify-between items-start mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-display text-base tracking-wide text-white">{healthyCred.name}</h3>
                  <Badge variant="green">正常可用</Badge>
                </div>
                <div className="text-xs text-muted">{healthyCred.description}</div>
              </div>
            </div>
            <div className="bg-black/30 p-4 rounded-lg border border-white/5 mb-5 font-mono text-xs text-muted/80 break-all leading-relaxed">
              API_KEY: sk_live_8f92<span className="text-muted/40">{'••••••••••••••••••••'}</span>3a1c<br />
              QUOTA: {healthyCred.quotaInfo}
            </div>
            <div className="mt-auto flex gap-3 border-t border-white/8 pt-4">
              <Button variant="outline" className="flex-1" onClick={() => addToast('打开配置编辑面板…', 'info')}>修改配置</Button>
              <button
                className="btn btn-outline flex-1 border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/10"
                onClick={handleTestConnection}
                disabled={testing}
              >
                {testing ? (
                  <>
                    <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeDasharray="32" className="opacity-30" />
                      <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                    </svg>
                    检测中…
                  </>
                ) : (
                  '连通性检测'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Expired credential */}
        {expiredCred && (
          <div className="glass-panel p-6 flex flex-col border border-[#F87171]/25 bg-[#F87171]/[0.03]">
            <div className="flex justify-between items-start mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-display text-base tracking-wide text-white">{expiredCred.name}</h3>
                  <Badge variant="red">已过期</Badge>
                </div>
                <div className="text-xs text-muted">{expiredCred.description}</div>
              </div>
            </div>
            <div className="bg-black/30 p-4 rounded-lg border border-[#F87171]/15 mb-5 font-mono text-xs text-red-400/80 break-all leading-relaxed">
              TOKEN: {expiredCred.maskedKey}<br />
              <span className="text-red-400">⚠ {expiredCred.expiryWarning}</span>
            </div>
            <div className="mt-auto flex gap-3 border-t border-[#F87171]/15 pt-4">
              <Button variant="outline" className="flex-1" onClick={() => addToast('打开凭证更新面板…', 'info')}>更新凭证</Button>
              <Button variant="danger" className="flex-1" onClick={() => addToast('已清除数据库覆盖值，回退至系统默认', 'info')}>清除覆盖值</Button>
            </div>
          </div>
        )}
      </div>

      {/* Global toggles */}
      <div className="glass-panel p-6">
        <div className="font-display text-sm tracking-wide mb-6">全局行为开关</div>
        <div className="divide-y divide-white/5">
          {MOCK_TOGGLES.map((toggle) => (
            <div key={toggle.id} className="flex items-center justify-between py-4">
              <div>
                <div className="text-sm text-starlight">{toggle.label}</div>
                <div className="text-xs text-muted mt-0.5">{toggle.description}</div>
              </div>
              <ToggleSwitch checked={toggleStates[toggle.id] ?? toggle.enabled} onChange={(v) => handleToggle(toggle.id, v)} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
