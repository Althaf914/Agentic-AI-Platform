import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { login as loginApi } from "@/api/auth";

export function useAuth() {
  const navigate = useNavigate();
  const { token, user, setAuth, clearAuth } = useAuthStore();

  const login = async (email: string, password: string) => {
    const data = await loginApi(email, password);
    setAuth(data.access_token, {
      id: data.user_id,
      email,
      role: data.role,
    });
    navigate("/dashboard");
  };

  const logout = () => {
    clearAuth();
    navigate("/login");
  };

  return {
    login,
    logout,
    user,
    role: user?.role ?? null,
    isAuthenticated: !!token,
  };
}
