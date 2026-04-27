import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  CustomSelect,
  DatePicker,
  DateTimePicker,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerShell,
  InputBox,
  NumberInput,
  SegmentedControl,
} from '@vistaflow/ui';
import { COMMON_LABELS, TASK_DRAWER_FORM_LABELS, TASK_DRAWER_LABELS } from '@/constants/labels';
import { useToastStore } from '@/stores/toastStore';
import { createTask, extractApiErrorMessage, fetchTaskTypes } from '@/services/taskService';
import type { TaskDateMode, TaskParamDefinition, TaskScheduleMode } from '@/types/task';
import {
  DEFAULT_CRON_EXPRESSION,
  DEFAULT_DATE_OFFSET_DAYS,
  buildTaskCreateRequest,
  findMissingRequiredParam,
  taskTypeSupportsDateMode,
} from './taskDrawerPayload';

interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

export function TaskDrawer({ isOpen, onClose, onSubmit }: TaskDrawerProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  const [taskName, setTaskName] = useState('');
  const [taskType, setTaskType] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleMode, setScheduleMode] = useState<TaskScheduleMode>('manual');
  const [cronExpr, setCronExpr] = useState(DEFAULT_CRON_EXPRESSION);
  const [runAt, setRunAt] = useState('');
  const [dateMode, setDateMode] = useState<TaskDateMode>('fixed');
  const [dateOffsetDays, setDateOffsetDays] = useState(String(DEFAULT_DATE_OFFSET_DAYS));
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

    if (!selectedTaskType.supportsCron && scheduleMode !== 'manual') {
      setScheduleMode('manual');
    }
  }, [scheduleMode, selectedTaskType]);

  useEffect(() => {
    if (selectedTaskType?.type === 'fetch-train-runs' && scheduleMode === 'cron') {
      setDateMode('relative');
    }
  }, [scheduleMode, selectedTaskType?.type]);

  useEffect(() => {
    if (isOpen) {
      return;
    }

    setTaskName('');
    setDescription('');
    setScheduleMode('manual');
    setCronExpr(DEFAULT_CRON_EXPRESSION);
    setRunAt('');
    setDateMode('fixed');
    setDateOffsetDays(String(DEFAULT_DATE_OFFSET_DAYS));
    setParamValues({});
  }, [isOpen]);

  const createTaskMutation = useMutation({
    mutationFn: createTask,
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

    const missingRequiredParam = findMissingRequiredParam(selectedTaskType, paramValues, dateMode);
    if (missingRequiredParam) {
      addToast(TASK_DRAWER_FORM_LABELS.requiredField(missingRequiredParam.label), 'warn');
      return;
    }

    const normalizedCron = scheduleMode === 'cron' ? cronExpr.trim() : '';
    if (scheduleMode === 'cron' && normalizedCron.length === 0) {
      addToast(TASK_DRAWER_FORM_LABELS.cronRequired, 'warn');
      return;
    }
    if (scheduleMode === 'once' && runAt.trim().length === 0) {
      addToast(TASK_DRAWER_FORM_LABELS.runAtRequired, 'warn');
      return;
    }
    if (taskTypeSupportsDateMode(selectedTaskType) && dateMode === 'relative') {
      const offset = Number.parseInt(dateOffsetDays, 10);
      if (!Number.isInteger(offset) || offset < 0 || offset > 60) {
        addToast(TASK_DRAWER_FORM_LABELS.dateOffsetInvalid, 'warn');
        return;
      }
    }

    createTaskMutation.mutate(
      buildTaskCreateRequest({
        name: normalizedName,
        taskType: selectedTaskType,
        description,
        enabled: true,
        scheduleMode,
        cronExpr,
        runAt,
        dateMode,
        dateOffsetDays,
        paramValues,
      }),
    );
  }

  const scheduleModeOptions = [
    { value: 'manual' as const, label: TASK_DRAWER_LABELS.scheduleManual },
    {
      value: 'once' as const,
      label: TASK_DRAWER_LABELS.scheduleOnce,
      disabled: !selectedTaskType?.supportsCron,
    },
    {
      value: 'cron' as const,
      label: TASK_DRAWER_LABELS.scheduleCron,
      disabled: !selectedTaskType?.supportsCron,
    },
  ];

  const dateModeOptions = [
    { value: 'fixed' as const, label: TASK_DRAWER_LABELS.dateModeFixed },
    { value: 'relative' as const, label: TASK_DRAWER_LABELS.dateModeRelative },
  ];

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

        <section className="vf-drawer-group">
          <div>
            <label className="vf-drawer-label">{TASK_DRAWER_LABELS.scheduleMode}</label>
            <SegmentedControl
              value={scheduleMode}
              onChange={setScheduleMode}
              options={scheduleModeOptions}
              className="mt-3"
            />
            {!selectedTaskType?.supportsCron ? (
              <div className="vf-drawer-meta mt-3">{TASK_DRAWER_FORM_LABELS.cronUnsupportedHint}</div>
            ) : null}
          </div>
          {scheduleMode === 'once' ? (
            <div>
              <label className="vf-drawer-label">{TASK_DRAWER_LABELS.runAt}</label>
              <DateTimePicker value={runAt} onChange={setRunAt} minDate={new Date()} />
              <div className="vf-drawer-meta mt-3">{TASK_DRAWER_FORM_LABELS.runAtHint}</div>
            </div>
          ) : null}
          {scheduleMode === 'cron' ? (
            <div>
              <label className="vf-drawer-label">{TASK_DRAWER_LABELS.cronExpr}</label>
              <InputBox
                className="w-full font-mono text-sm text-[#8B5CF6]"
                value={cronExpr}
                onChange={(event) => setCronExpr(event.target.value)}
                placeholder="0 3 * * *"
              />
              <div className="vf-drawer-meta mt-3">{TASK_DRAWER_FORM_LABELS.cronManualHint}</div>
            </div>
          ) : null}
        </section>

        {selectedTaskType?.paramSchema.length ? (
          <section className="vf-drawer-group">
            {selectedTaskType.paramSchema.map((param) => (
              <div key={param.key}>
                <label className="vf-drawer-label">
                  {param.label}
                  {param.required ? ' *' : ''}
                </label>
                {param.valueType === 'date' && taskTypeSupportsDateMode(selectedTaskType) ? (
                  <div className="space-y-3">
                    <SegmentedControl
                      value={dateMode}
                      onChange={setDateMode}
                      options={dateModeOptions}
                      size="sm"
                    />
                    {dateMode === 'fixed' ? (
                      <DatePicker
                        value={paramValues[param.key] ?? ''}
                        onChange={(value) => updateParamValue(param, value)}
                        appearance="boxed"
                        className="w-full"
                        minDate={new Date()}
                      />
                    ) : (
                      <NumberInput
                        className="w-full"
                        min={0}
                        max={60}
                        value={dateOffsetDays}
                        onChange={(event) => setDateOffsetDays(event.target.value)}
                        placeholder={TASK_DRAWER_LABELS.dateOffsetPlaceholder}
                      />
                    )}
                  </div>
                ) : param.valueType === 'date' ? (
                  <DatePicker
                    value={paramValues[param.key] ?? ''}
                    onChange={(value) => updateParamValue(param, value)}
                    appearance="boxed"
                    className="w-full"
                    minDate={new Date()}
                  />
                ) : (
                  <InputBox
                    className="w-full"
                    type="text"
                    placeholder={param.placeholder}
                    value={paramValues[param.key] ?? ''}
                    onChange={(event) => updateParamValue(param, event.target.value)}
                  />
                )}
                <div className="vf-drawer-meta mt-3">{param.description}</div>
              </div>
            ))}
          </section>
        ) : null}

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
