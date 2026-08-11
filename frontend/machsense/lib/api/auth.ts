import { api, setAuthToken, getAuthToken } from "./client";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
  name: string;
}

export interface UserOut {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>("/auth/login", { email, password }),

  me: () => api.get<UserOut>("/auth/me"),

  logout: () => {
    setAuthToken(null);
  },

  saveToken: (token: string) => setAuthToken(token),
  getToken: () => getAuthToken(),
};
