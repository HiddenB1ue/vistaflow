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
import { createTask, extractApiErrorMessage, fetchTaskTypes } from '@/services/taskService';
import { useToastStore } from '@/stores/toastStore';
import {
  buildTaskCreateRequest,
  findMissingRequiredParam,
  taskTypeSupportsDateMode,
} from './taskDrawerPayload';
import { useTaskDrawerForm } from './useTaskDrawerForm';

interface TaskDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskName: string) => void;
}

export function TaskDrawer({ isOpen, onClose, onSubmit }: TaskDrawerProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

  const { data: taskTypes = [], isLoading: taskTypesLoading } = useQuery({
    queryKey: ['admin', 'task-types'],
    queryFn: fetchTaskTypes,
    enabled: isOpen,
  });

  const {
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
  } = useTaskDrawerForm(isOpen, taskTypes);

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
