import { useEffect, useMemo, useState } from 'react';
import { TASK_DRAWER_FORM_LABELS, TASK_DRAWER_LABELS } from '@/constants/labels';
import type {
  TaskDateMode,
  TaskParamDefinition,
  TaskScheduleMode,
  TaskTypeDefinition,
} from '@/types/task';
import {
  DEFAULT_CRON_EXPRESSION,
  DEFAULT_DATE_OFFSET_DAYS,
} from './taskDrawerPayload';

export function useTaskDrawerForm(
  isOpen: boolean,
  taskTypes: TaskTypeDefinition[],
) {
  const [taskName, setTaskName] = useState('');
  const [taskType, setTaskType] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleMode, setScheduleMode] = useState<TaskScheduleMode>('manual');
  const [cronExpr, setCronExpr] = useState(DEFAULT_CRON_EXPRESSION);
  const [runAt, setRunAt] = useState('');
  const [dateMode, setDateMode] = useState<TaskDateMode>('fixed');
  const [dateOffsetDays, setDateOffsetDays] = useState(String(DEFAULT_DATE_OFFSET_DAYS));
  const [paramValues, setParamValues] = useState<Record<string, string>>({});

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

  function updateParamValue(param: TaskParamDefinition, value: string) {
    setParamValues((currentValues) => ({
      ...currentValues,
      [param.key]: value,
    }));
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

  return {
    taskName,
    setTaskName,
    taskType,
    setTaskType,
    description,
    setDescription,
    scheduleMode,
    setScheduleMode,
    cronExpr,
    setCronExpr,
    runAt,
    setRunAt,
    dateMode,
    setDateMode,
    dateOffsetDays,
    setDateOffsetDays,
    paramValues,
    updateParamValue,
    taskTypeOptions,
    selectedTaskType,
    scheduleModeOptions,
    dateModeOptions,
  };
}
