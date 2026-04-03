import { createApiClient } from '@vistaflow/api-client';

export const apiClient = createApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
});
