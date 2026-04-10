
import { createDefaultAppApiClient } from '@vistaflow/api-client';

export const apiClient = createDefaultAppApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
});

// 延迟导入 tokenStorage 避免循环依赖
let tokenStorageModule: typeof import('@/utils/tokenStorage').tokenStorage | null = null;

async function getTokenStorage() {
  if (!tokenStorageModule) {
    const module = await import('@/utils/tokenStorage');
    tokenStorageModule = module.tokenStorage;
  }
  return tokenStorageModule;
}

// 请求拦截器：自动添加 token
apiClient.interceptors.request.use(async (config) => {
  const tokenStorage = await getTokenStorage();
  const token = tokenStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理 401 错误
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const tokenStorage = await getTokenStorage();
      tokenStorage.removeToken();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
