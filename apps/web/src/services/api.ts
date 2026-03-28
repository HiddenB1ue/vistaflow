import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    // 统一错误处理，不暴露敏感信息
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      if (status === 401) {
        localStorage.removeItem('token');
      }
    }
    return Promise.reject(error);
  },
);
