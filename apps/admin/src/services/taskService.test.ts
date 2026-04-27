import { describe, it, expect } from 'vitest';
import { fetchTasks } from './taskService';

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
});
