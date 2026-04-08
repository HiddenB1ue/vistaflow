
import { createDefaultAppApiClient } from '@vistaflow/api-client';

export const apiClient = createDefaultAppApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
});
