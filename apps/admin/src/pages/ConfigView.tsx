import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CONFIG_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import { fetchCredentials, fetchToggles } from '@/services/configService';
import { useToastStore } from '@/stores/toastStore';
import { Badge, Button, PanelBody, PanelCard, SectionHeader, ToggleSwitch } from '@vistaflow/ui';

export default function ConfigView() {
  const addToast = useToastStore((state) => state.addToast);
  const [testing, setTesting] = useState(false);
  const [toggleStates, setToggleStates] = useState<Record<string, boolean>>({});

  const { data: credentials = [] } = useQuery({
    queryKey: ['admin', 'credentials'],
    queryFn: fetchCredentials,
  });

  const { data: toggles = [] } = useQuery({
    queryKey: ['admin', 'toggles'],
    queryFn: fetchToggles,
  });

  useEffect(() => {
    if (toggles.length === 0) return;
    setToggleStates(Object.fromEntries(toggles.map((toggle) => [toggle.id, toggle.enabled])));
  }, [toggles]);

  const handleTestConnection = () => {
    setTesting(true);
    setTimeout(() => {
      setTesting(false);
      addToast(CONFIG_LABELS.connectionOk, 'success');
    }, 1600);
  };

  const healthyCred = credentials.find((credential) => credential.health === 'healthy');
  const expiredCred = credentials.find((credential) => credential.health === 'expired');

  return (
    <div className="vf-page-stack">
      <p className="max-w-2xl text-sm leading-relaxed text-muted">{CONFIG_LABELS.description}</p>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {healthyCred && (
          <PanelCard>
            <SectionHeader
              eyebrow={CONFIG_LABELS.credentialEyebrow}
              title={healthyCred.name}
              subtitle={healthyCred.description}
              actions={<Badge variant="green">{CONFIG_LABELS.healthyStatus}</Badge>}
            />
            <PanelBody>
              <div className="break-all rounded-lg border border-white/5 bg-black/30 p-4 font-mono text-xs leading-relaxed text-muted/80">
                <div>API_KEY: {healthyCred.maskedKey}</div>
                {healthyCred.quotaInfo ? <div>{healthyCred.quotaInfo}</div> : null}
              </div>
              <div className="flex gap-3 border-t border-white/8 pt-4">
                <Button variant="outline" className="flex-1" onClick={() => addToast(TOAST_MESSAGES.featureInDev(CONFIG_LABELS.credentialEditorInDev), 'info')}>
                  {CONFIG_LABELS.editConfig}
                </Button>
                <Button variant="outline" className="flex-1 border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/10" onClick={handleTestConnection} disabled={testing}>
                  {testing ? (
                    <>
                      <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeDasharray="32" className="opacity-30" />
                        <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                      </svg>
                      {CONFIG_LABELS.testing}
                    </>
                  ) : (
                    CONFIG_LABELS.testConnection
                  )}
                </Button>
              </div>
            </PanelBody>
          </PanelCard>
        )}

        {expiredCred && (
          <PanelCard className="border border-[#F87171]/25 bg-[#F87171]/[0.03]">
            <SectionHeader
              eyebrow={CONFIG_LABELS.credentialEyebrow}
              title={expiredCred.name}
              subtitle={expiredCred.description}
              actions={<Badge variant="red">{CONFIG_LABELS.expiredStatus}</Badge>}
            />
            <PanelBody>
              <div className="break-all rounded-lg border border-[#F87171]/15 bg-black/30 p-4 font-mono text-xs leading-relaxed text-red-400/80">
                <div>TOKEN: {expiredCred.maskedKey}</div>
                {expiredCred.expiryWarning ? <div className="text-red-400">{expiredCred.expiryWarning}</div> : null}
              </div>
              <div className="flex gap-3 border-t border-[#F87171]/15 pt-4">
                <Button variant="outline" className="flex-1" onClick={() => addToast(TOAST_MESSAGES.featureInDev(CONFIG_LABELS.updatePanelInDev), 'info')}>
                  {CONFIG_LABELS.updateCredential}
                </Button>
                <Button variant="danger" className="flex-1" onClick={() => addToast(CONFIG_LABELS.overrideCleared, 'info')}>
                  {CONFIG_LABELS.clearOverride}
                </Button>
              </div>
            </PanelBody>
          </PanelCard>
        )}
      </div>

      <PanelCard>
        <SectionHeader eyebrow={CONFIG_LABELS.runtimeEyebrow} title={CONFIG_LABELS.globalToggles} subtitle={CONFIG_LABELS.togglesSubtitle} />
        <PanelBody className="divide-y divide-white/5">
          {toggles.map((toggle) => (
            <div key={toggle.id} className="flex items-center justify-between gap-4 py-4">
              <div>
                <div className="text-sm text-starlight">{toggle.label}</div>
                <div className="mt-0.5 text-xs text-muted">{toggle.description}</div>
              </div>
              <ToggleSwitch checked={toggleStates[toggle.id] ?? toggle.enabled} onChange={(value) => setToggleStates((prev) => ({ ...prev, [toggle.id]: value }))} />
            </div>
          ))}
        </PanelBody>
      </PanelCard>
    </div>
  );
}
