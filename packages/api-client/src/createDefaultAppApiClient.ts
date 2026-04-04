import type { AxiosInstance } from 'axios';
import { createApiClient, type ApiClientOptions } from './createApiClient';

export interface DefaultAppApiClientOptions extends Omit<ApiClientOptions, 'baseURL'> {
  baseURL?: string;
}

export function createDefaultAppApiClient(options: DefaultAppApiClientOptions = {}): AxiosInstance {
  const { baseURL = '/api', ...rest } = options;
  return createApiClient({
    baseURL,
    ...rest,
  });
}
