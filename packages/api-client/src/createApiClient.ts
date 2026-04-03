import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

export interface ApiClientOptions {
  baseURL: string;
  timeout?: number;
  getToken?: () => string | null;
  onUnauthorized?: () => void;
  requestInterceptors?: Array<(config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig>;
  responseInterceptors?: Array<(response: AxiosResponse) => AxiosResponse>;
}

export function createApiClient(options: ApiClientOptions): AxiosInstance {
  const {
    baseURL,
    timeout = 10000,
    getToken = () => localStorage.getItem('token'),
    onUnauthorized = () => localStorage.removeItem('token'),
    requestInterceptors = [],
    responseInterceptors = [],
  } = options;

  const instance = axios.create({
    baseURL,
    timeout,
    headers: { 'Content-Type': 'application/json' },
  });

  // Built-in request interceptor: attach Bearer token
  instance.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Built-in response interceptor: handle 401
  instance.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401) {
          onUnauthorized();
        }
      }
      return Promise.reject(error);
    },
  );

  // Custom interceptors applied after built-in ones
  for (const interceptor of requestInterceptors) {
    instance.interceptors.request.use(interceptor);
  }

  for (const interceptor of responseInterceptors) {
    instance.interceptors.response.use(interceptor);
  }

  return instance;
}
