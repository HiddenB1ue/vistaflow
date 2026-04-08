import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  CustomSelect,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
  ToggleSwitch,
} from '@vistaflow/ui';
import { COMMON_LABELS, TASK_DRAWER_FORM_LABELS, TASK_DRAWER_LABELS } from '@/constants/labels';
import { useToastStore } from '@/stores/toastStore';
import { createTask, extractApiErrorMessage, fetchTaskTypes } from '@/services/taskService';
import type { TaskCreateRequest, TaskParamDefinition, TaskTypeDefinition } from '@/types/task';

interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

const DEFAULT_CRON_EXPRESSION = '0 0/15 * * * ?';

function buildPayload(
  taskType: TaskTypeDefinition | undefined,
  paramValues: Record<string, string>,
): Record<string, string> {
  if (!taskType) {
    return {};
  }

  const payloadEntries = taskType.paramSchema.flatMap((param) => {
    const value = (paramValues[param.key] ?? '').trim();
    if (!value) {
      return [];
    }
    return [[param.key, value] as const];
  });

  return Object.fromEntries(payloadEntries);
}

export function TaskDrawer({ isOpen, onClose, onSubmit }: TaskDrawerProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  const [taskName, setTaskName] = useState('');
  const [taskType, setTaskType] = useState('');
  const [description, setDescription] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [cronEnabled, setCronEnabled] = useState(false);
  const [cronExpr, setCronExpr] = useState(DEFAULT_CRON_EXPRESSION);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});

  const { data: taskTypes = [], isLoading: taskTypesLoading } = useQuery({
    queryKey: ['admin', 'task-types'],
    queryFn: fetchTaskTypes,
    enabled: isOpen,
  });

  const taskTypeOptions = useMemo(
    () =>
      taskTypes.map((item) => ({
        value: item.type,
        label: item.implemented ? item.label : `${item.label}（${TASK_DRAWER_FORM_LABELS.reservedTag}）`,
      })),
    [taskTypes],
  );

  const selectedTaskType = useMemo(
    () => taskTypes.find((candidate) => candidate.type === taskType),
    [taskType, taskTypes],
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const firstTaskType = taskTypes[0];
    if (!firstTaskType) {
      return;
    }

    if (!taskType || !taskTypes.some((candidate) => candidate.type === taskType)) {
      setTaskType(firstTaskType.type);
    }
  }, [isOpen, taskType, taskTypes]);

  useEffect(() => {
    if (!selectedTaskType) {
      return;
    }

    setParamValues((currentValues) =>
      Object.fromEntries(
        selectedTaskType.paramSchema.map((param) => [param.key, currentValues[param.key] ?? '']),
      ),
    );

    if (!selectedTaskType.supportsCron) {
      setCronEnabled(false);
    }
  }, [selectedTaskType]);

  useEffect(() => {
    if (isOpen) {
      return;
    }

    setTaskName('');
    setDescription('');
    setEnabled(true);
    setCronEnabled(false);
    setCronExpr(DEFAULT_CRON_EXPRESSION);
    setParamValues({});
  }, [isOpen]);

  const createTaskMutation = useMutation({
    mutationFn: (payload: TaskCreateRequest) => createTask(payload),
    onSuccess: async (createdTask) => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'tasks'] });
      onSubmit(createdTask.name);
      onClose();
    },
    onError: (error: unknown) => {
      addToast(extractApiErrorMessage(error), 'error');
    },
  });

  function updateParamValue(param: TaskParamDefinition, value: string) {
    setParamValues((currentValues) => ({
      ...currentValues,
      [param.key]: value,
    }));
  }

  function handleSubmit() {
    const normalizedName = taskName.trim();
    if (!normalizedName) {
      addToast(TASK_DRAWER_FORM_LABELS.nameRequired, 'warn');
      return;
    }

    if (!selectedTaskType) {
      addToast(TASK_DRAWER_FORM_LABELS.typeUnavailable, 'error');
      return;
    }

    const missingRequiredParam = selectedTaskType.paramSchema.find((param) => {
      if (!param.required) {
        return false;
      }
      return (paramValues[param.key] ?? '').trim().length === 0;
    });
    if (missingRequiredParam) {
      addToast(TASK_DRAWER_FORM_LABELS.requiredField(missingRequiredParam.label), 'warn');
      return;
    }

    const normalizedCron = cronEnabled ? cronExpr.trim() : '';
    if (cronEnabled && normalizedCron.length === 0) {
      addToast(TASK_DRAWER_FORM_LABELS.cronRequired, 'warn');
      return;
    }

    createTaskMutation.mutate({
      name: normalizedName,
      type: selectedTaskType.type,
      description: description.trim() || undefined,
      enabled,
      cron: cronEnabled ? normalizedCron : null,
      payload: buildPayload(selectedTaskType, paramValues),
    });
  }

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={TASK_DRAWER_LABELS.eyebrow}
        title={TASK_DRAWER_LABELS.title}
        subtitle={TASK_DRAWER_LABELS.subtitle}
        onClose={onClose}
        closeLabel={COMMON_LABELS.close}
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.name}</label>
            <InputBox
              className="w-full"
              placeholder={TASK_DRAWER_LABELS.namePlaceholder}
              value={taskName}
              onChange={(event) => setTaskName(event.target.value)}
            />
          </div>
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.type}</label>
            <CustomSelect
              options={taskTypeOptions}
              value={taskType}
              onChange={setTaskType}
              className="w-full"
            />
            {selectedTaskType ? (
              <div className="vf-drawer-meta mt-3">{selectedTaskType.description}</div>
            ) : null}
            {taskTypesLoading ? (
              <div className="vf-drawer-meta mt-3">{TASK_DRAWER_FORM_LABELS.loadingTypes}</div>
            ) : null}
          </div>
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_FORM_LABELS.description}</label>
            <InputBox
              className="w-full"
              placeholder={TASK_DRAWER_FORM_LABELS.descriptionPlaceholder}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
        </section>

        {selectedTaskType?.paramSchema.length ? (
          <section className="vf-drawer-group">
            {selectedTaskType.paramSchema.map((param) => (
              <div key={param.key}>
                <label className="vf-drawer-label">
                  {param.label}
                  {param.required ? ' *' : ''}
                </label>
                <InputBox
                  className="w-full"
                  type={param.valueType === 'date' ? 'date' : 'text'}
                  placeholder={param.placeholder}
                  value={paramValues[param.key] ?? ''}
                  onChange={(event) => updateParamValue(param, event.target.value)}
                />
                <div className="vf-drawer-meta mt-3">{param.description}</div>
              </div>
            ))}
          </section>
        ) : null}

        <section className="vf-drawer-group">
          <div className="vf-drawer-toggle-row">
            <span className="vf-drawer-toggle-row__title">{TASK_DRAWER_FORM_LABELS.enabled}</span>
            <ToggleSwitch checked={enabled} onChange={setEnabled} />
          </div>
          <div className="vf-drawer-toggle-row">
            <span className="vf-drawer-toggle-row__title">{TASK_DRAWER_LABELS.cronEnabled}</span>
            <ToggleSwitch
              checked={cronEnabled}
              onChange={selectedTaskType?.supportsCron ? setCronEnabled : () => undefined}
            />
          </div>
          <div className={!cronEnabled || !selectedTaskType?.supportsCron ? 'opacity-35' : ''}>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.cronExpr}</label>
            <InputBox
              className="w-full font-mono text-sm text-[#8B5CF6]"
              value={cronExpr}
              onChange={(event) => setCronExpr(event.target.value)}
              placeholder="* * * * * *"
              disabled={!cronEnabled || !selectedTaskType?.supportsCron}
            />
            <div className="vf-drawer-meta mt-3">
              {selectedTaskType?.supportsCron
                ? TASK_DRAWER_FORM_LABELS.cronManualHint
                : TASK_DRAWER_FORM_LABELS.cronUnsupportedHint}
            </div>
          </div>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="outline" onClick={onClose} disabled={createTaskMutation.isPending}>
          {COMMON_LABELS.cancel}
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmit}
          disabled={createTaskMutation.isPending || taskTypesLoading}
        >
          {createTaskMutation.isPending ? TASK_DRAWER_FORM_LABELS.submitting : TASK_DRAWER_LABELS.submit}
        </Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
