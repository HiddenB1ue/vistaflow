import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CONFIG_LABELS } from '@/constants/labels';
import { fetchSystemSettings, updateSystemSettings } from '@/services/configService';
import { extractApiErrorMessage } from '@/services/taskService';
import { useToastStore } from '@/stores/toastStore';
import type { SystemSetting, SystemSettingValue } from '@/types/config';
import { Button, InputBox, PanelBody, PanelCard, SectionHeader, ToggleSwitch } from '@vistaflow/ui';

interface SettingDraft {
  value: SystemSettingValue;
  enabled: boolean;
}

export default function ConfigView() {
  const addToast = useToastStore((state) => state.addToast);
  const queryClient = useQueryClient();
  const [drafts, setDrafts] = useState<Record<string, SettingDraft>>({});
  const [savingToggleKey, setSavingToggleKey] = useState<string | null>(null);
  const [isSavingIntegration, setIsSavingIntegration] = useState(false);
  const refreshPriorityKeysRef = useRef<Set<string>>(new Set());

  const { data: settings = [] } = useQuery({
    queryKey: ['admin', 'system-settings'],
    queryFn: fetchSystemSettings,
  });

  function draftEqualsSetting(draft: SettingDraft | undefined, setting: SystemSetting): boolean {
    if (!draft) {
      return true;
    }
    return (
      JSON.stringify(draft.value) === JSON.stringify(setting.value) &&
      draft.enabled === setting.enabled
    );
  }

  useEffect(() => {
    if (settings.length === 0) {
      return;
    }
    setDrafts((current) => {
      const next = { ...current };
      for (const setting of settings) {
        const shouldRefresh =
          refreshPriorityKeysRef.current.has(setting.key) ||
          draftEqualsSetting(current[setting.key], setting);
        if (shouldRefresh) {
          next[setting.key] = {
            value: setting.value,
            enabled: setting.enabled,
          };
        }
      }
      refreshPriorityKeysRef.current.clear();
      return next;
    });
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: updateSystemSettings,
    onSuccess: async (result) => {
      refreshPriorityKeysRef.current = new Set(result.updatedKeys);
      await queryClient.invalidateQueries({ queryKey: ['admin', 'system-settings'] });
    },
    onError: (error: unknown, variables) => {
      const firstItem = variables.items[0];
      const singleToggle =
        variables.items.length === 1 &&
        firstItem !== undefined &&
        toggleSettings.some((item) => item.key === firstItem.key);
      if (singleToggle && firstItem !== undefined) {
        const key = firstItem.key;
        const original = settings.find((item) => item.key === key);
        if (original) {
          setDrafts((current) => ({
            ...current,
            [key]: {
              value: original.value,
              enabled: original.enabled,
            },
          }));
        }
      }
      addToast(extractApiErrorMessage(error), 'error');
    },
    onSettled: () => {
      setSavingToggleKey(null);
      setIsSavingIntegration(false);
    },
  });

  const integrationSettings = useMemo(
    () => settings.filter((setting) => ['amap', 'ticket_12306'].includes(setting.category)),
    [settings],
  );

  const toggleSettings = useMemo(
    () => settings.filter((setting) => ['task', 'system'].includes(setting.category) && setting.valueType === 'bool'),
    [settings],
  );

  function getDraft(setting: SystemSetting): SettingDraft {
    return (
      drafts[setting.key] ?? {
        value: setting.value,
        enabled: setting.enabled,
      }
    );
  }

  function isDirty(setting: SystemSetting): boolean {
    const draft = getDraft(setting);
    return JSON.stringify(draft.value) !== JSON.stringify(setting.value) || draft.enabled !== setting.enabled;
  }

  function updateDraftValue(setting: SystemSetting, value: SystemSettingValue) {
    setDrafts((current) => ({
      ...current,
      [setting.key]: {
        enabled: current[setting.key]?.enabled ?? setting.enabled,
        value,
      },
    }));
  }

  const integrationDirtySettings = useMemo(
    () => integrationSettings.filter((setting) => isDirty(setting)),
    [integrationSettings, drafts],
  );

  function handleSaveIntegrationSettings() {
    if (integrationDirtySettings.length === 0) {
      return;
    }
    setIsSavingIntegration(true);
    updateMutation.mutate(
      {
        items: integrationDirtySettings.map((setting) => {
          const draft = getDraft(setting);
          return {
            key: setting.key,
            value: draft.value,
            enabled: draft.enabled,
          };
        }),
      },
      {
        onSuccess: () => {
          addToast(CONFIG_LABELS.saveSuccess, 'success');
        },
      },
    );
  }

  function handleToggleChange(setting: SystemSetting, value: boolean) {
    if (updateMutation.isPending) {
      return;
    }
    setDrafts((current) => ({
      ...current,
      [setting.key]: {
        value,
        enabled: current[setting.key]?.enabled ?? setting.enabled,
      },
    }));
    setSavingToggleKey(setting.key);
    updateMutation.mutate(
      {
        items: [
          {
            key: setting.key,
            value,
            enabled: getDraft(setting).enabled,
          },
        ],
      },
      {
        onSuccess: () => {
          addToast(CONFIG_LABELS.saveSuccess, 'success');
        },
      },
    );
  }

  return (
    <div className="vf-page-stack">
      <p className="max-w-2xl text-sm leading-relaxed text-muted">{CONFIG_LABELS.description}</p>

      <PanelCard>
        <SectionHeader
          eyebrow={CONFIG_LABELS.integrationEyebrow}
          title={CONFIG_LABELS.integrationSettings}
          subtitle={CONFIG_LABELS.integrationSubtitle}
          actions={
            <div className="flex items-center gap-3">
              {integrationDirtySettings.length > 0 ? (
                <div className="text-xs text-muted">{CONFIG_LABELS.integrationChangedCount(integrationDirtySettings.length)}</div>
              ) : null}
              <Button
                variant="outline"
                onClick={handleSaveIntegrationSettings}
                disabled={integrationDirtySettings.length === 0 || isSavingIntegration || updateMutation.isPending}
              >
                {isSavingIntegration ? CONFIG_LABELS.saving : CONFIG_LABELS.saveIntegrationSettings}
              </Button>
            </div>
          }
        />
        <PanelBody className="divide-y divide-white/5">
          {integrationSettings.map((setting) => {
            const draft = getDraft(setting);
            return (
              <div key={setting.key} className="py-4">
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-starlight">{setting.label}</div>
                  <div className="mt-0.5 text-xs text-muted">{setting.description}</div>
                  {setting.valueType === 'bool' ? (
                    <div className="mt-4">
                      <ToggleSwitch
                        checked={Boolean(draft.value)}
                        onChange={(value) => updateDraftValue(setting, value)}
                      />
                    </div>
                  ) : (
                    <>
                      <div className="mt-3 text-[11px] uppercase tracking-[0.24em] text-muted/60">
                        {CONFIG_LABELS.settingValue}
                      </div>
                      <InputBox
                        className="mt-2 w-full font-mono text-sm"
                        value={String(draft.value ?? '')}
                        placeholder={CONFIG_LABELS.emptyValueHint}
                        onChange={(event) => updateDraftValue(setting, event.target.value)}
                      />
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </PanelBody>
      </PanelCard>

      <PanelCard>
        <SectionHeader
          eyebrow={CONFIG_LABELS.runtimeEyebrow}
          title={CONFIG_LABELS.globalToggles}
          subtitle={CONFIG_LABELS.togglesSubtitle}
        />
        <PanelBody className="divide-y divide-white/5">
          {toggleSettings.map((setting) => {
            const draft = getDraft(setting);
            const isSaving = savingToggleKey === setting.key && updateMutation.isPending;
            return (
              <div key={setting.key} className="flex flex-col gap-3 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-starlight">{setting.label}</div>
                  <div className="mt-0.5 text-xs text-muted">{setting.description}</div>
                </div>
                <div className="flex items-center gap-3">
                  <ToggleSwitch
                    checked={Boolean(draft.value)}
                    onChange={(value) => handleToggleChange(setting, value)}
                  />
                  {isSaving ? <div className="text-xs text-muted">{CONFIG_LABELS.saving}</div> : null}
                </div>
              </div>
            );
          })}
        </PanelBody>
      </PanelCard>
    </div>
  );
}
