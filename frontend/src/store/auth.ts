import axios from "axios";
import { create } from "zustand";
import { persist } from "zustand/middleware";

const baseURL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  institution_name?: string;
  institution_phone?: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  setSession: (access: string, refresh: string, user: AuthUser) => void;
  refreshAccessToken: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setSession: (accessToken, refreshToken, user) =>
        set({ accessToken, refreshToken, user }),

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) throw new Error("No refresh token");
        const { data } = await axios.post(`${baseURL}/auth/refresh/`, {
          refresh: refreshToken,
        });
        set({ accessToken: data.access });
      },

      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "smart-school-auth" }
  )
);
