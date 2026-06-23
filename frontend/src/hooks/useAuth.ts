import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { User, AuthResponse } from "../types";

interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const login = useCallback(
    async (username: string, password: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.post<AuthResponse>(
          "/accounts/token/",
          {
            username,
            password,
          },
        );

        const { access } = response.data;
        localStorage.setItem("access_token", access);

        // Get current user
        const meResponse = await apiClient.get<User>("/accounts/me/");
        setUser(meResponse.data);

        navigate("/applications");
      } catch (err: any) {
        const message = err.response?.data?.error?.message || "Login failed";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await apiClient.post("/accounts/logout/");
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
      setIsLoading(false);
      navigate("/login");
    }
  }, [navigate]);

  return {
    user,
    isLoading,
    error,
    login,
    logout,
    isAuthenticated: !!localStorage.getItem("access_token"),
  };
}
