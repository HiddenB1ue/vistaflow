import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiClient } from './api';
import { createTask, deleteTask, fetchTask, fetchTasks, updateTask } from './taskService';
import type { Task } from '@/types/task';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const sampleTask: Task = {
  id: 1,
  name: 'Fetch stations',
  type: 'fetch-station',
  typeLabel: 'Fetch stations',
  status: 'idle',
  enabled: true,
  payload: {},
  metrics: { label: 'records', value: '0' },
  timing: { label: 'last run', value: '-' },
  latestRun: null,
};

describe('taskService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchTasks forwards query parameters to the API', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: {
        data: {
          items: [sampleTask],
          page: 1,
          pageSize: 20,
          total: 1,
          totalPages: 1,
        },
      },
    });

    const tasks = await fetchTasks({
      page: 1,
      pageSize: 20,
      keyword: ' station ',
      status: 'idle',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/admin/tasks', {
      params: {
        page: 1,
        pageSize: 20,
        keyword: 'station',
        status: 'idle',
      },
    });
    expect(tasks.items).toEqual([sampleTask]);
  });

  it('createTask unwraps the API response', async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: { data: sampleTask } });

    const created = await createTask({
      name: 'Fetch stations',
      type: 'fetch-station',
      payload: {},
    });

    expect(apiClient.post).toHaveBeenCalledWith('/admin/tasks', {
      name: 'Fetch stations',
      type: 'fetch-station',
      payload: {},
    });
    expect(created).toEqual(sampleTask);
  });

  it('updateTask patches a task and unwraps the API response', async () => {
    const updated = { ...sampleTask, enabled: false };
    (apiClient.patch as Mock).mockResolvedValueOnce({ data: { data: updated } });

    await expect(updateTask(1, { enabled: false })).resolves.toEqual(updated);
    expect(apiClient.patch).toHaveBeenCalledWith('/admin/tasks/1', { enabled: false });
  });

  it('deleteTask calls the API endpoint', async () => {
    (apiClient.delete as Mock).mockResolvedValueOnce({});

    await deleteTask(1);

    expect(apiClient.delete).toHaveBeenCalledWith('/admin/tasks/1');
  });

  it('fetchTask unwraps the API response', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: { data: sampleTask } });

    await expect(fetchTask(1)).resolves.toEqual(sampleTask);
    expect(apiClient.get).toHaveBeenCalledWith('/admin/tasks/1');
  });
});
