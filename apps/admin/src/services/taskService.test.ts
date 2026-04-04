import { describe, it, expect } from 'vitest';
import { fetchTasks } from './taskService';

describe('taskService', () => {
  it('fetchTasks returns mock data in mock mode', async () => {
    const tasks = await fetchTasks();
    expect(Array.isArray(tasks)).toBe(true);
    expect(tasks.length).toBeGreaterThan(0);
    for (const task of tasks) {
      expect(task).toHaveProperty('id');
      expect(task).toHaveProperty('name');
      expect(task).toHaveProperty('status');
    }
  });
});
