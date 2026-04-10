import { apiClient } from './api';
import { tokenStorage } from '@/utils/tokenStorage';

interface LoginResponse {
  token: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<string> {
    const response = await apiClient.post<{ data: LoginResponse }>('/login', credentials);
    const token = response.data.data.token;
    tokenStorage.setToken(token);
    return token;
  },

  logout(): void {
    tokenStorage.removeToken();
  },

  getToken(): string | null {
    return tokenStorage.getToken();
  },

  isAuthenticated(): boolean {
    return tokenStorage.hasToken();
  },
};
