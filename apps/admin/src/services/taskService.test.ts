import { describe, it, expect } from 'vitest';
import { createTask, deleteTask, fetchTask, fetchTasks, updateTask } from './taskService';

describe('taskService', () => {
  it('fetchTasks returns mock data in mock mode', async () => {
    const tasks = await fetchTasks({
      page: 1,
      pageSize: 20,
      keyword: '',
      status: 'all',
    });
    expect(Array.isArray(tasks.items)).toBe(true);
    expect(tasks.items.length).toBeGreaterThan(0);
    for (const task of tasks.items) {
      expect(task).toHaveProperty('id');
      expect(task).toHaveProperty('name');
      expect(task).toHaveProperty('status');
    }
  });

  it('updateTask toggles enabled in mock mode', async () => {
    const created = await createTask({
      name: `Mock toggle ${Date.now()}`,
      type: 'fetch-station',
      scheduleMode: 'cron',
      cron: '0 3 * * *',
      payload: {},
    });

    const disabled = await updateTask(created.id, { enabled: false });
    expect(disabled.enabled).toBe(false);

    const enabled = await updateTask(created.id, { enabled: true });
    expect(enabled.enabled).toBe(true);
  });

  it('deleteTask removes mock task state', async () => {
    const created = await createTask({
      name: `Mock delete ${Date.now()}`,
      type: 'fetch-station',
      payload: {},
    });

    await deleteTask(created.id);

    await expect(fetchTask(created.id)).rejects.toThrow();
  });
});
