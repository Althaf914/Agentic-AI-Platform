import { create } from "zustand";

interface User {
  id: string;
  email: string;
  role: "admin" | "sales" | "viewer";
}

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("agentforge_token"),
  user: (() => {
    const stored = localStorage.getItem("agentforge_user");
    return stored ? JSON.parse(stored) : null;
  })(),

  setAuth: (token, user) => {
    localStorage.setItem("agentforge_token", token);
    localStorage.setItem("agentforge_user", JSON.stringify(user));
    set({ token, user });
  },

  clearAuth: () => {
    localStorage.removeItem("agentforge_token");
    localStorage.removeItem("agentforge_user");
    set({ token: null, user: null });
  },
}));
