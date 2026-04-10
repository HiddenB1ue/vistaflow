const TOKEN_STORAGE_KEY = 'token';

export const ADMIN_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';
export const ADMIN_USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

function getBrowserStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage;
}

export function readAdminToken(): string {
  return getBrowserStorage()?.getItem(TOKEN_STORAGE_KEY) ?? '';
}

export function saveAdminToken(token: string): void {
  const storage = getBrowserStorage();
  if (!storage) {
    return;
  }

  storage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAdminToken(): void {
  getBrowserStorage()?.removeItem(TOKEN_STORAGE_KEY);
}
