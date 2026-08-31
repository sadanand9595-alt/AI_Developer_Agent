import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, ApiError, setToken } from "../api/client";
import type { TokenResponse, User } from "../api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    name: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCurrentUser = useCallback(async () => {
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me);
    } catch {
      // No valid session -- not an error state, just logged out.
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      try {
        const token = await api.post<TokenResponse>("/auth/login", {
          email,
          password,
        });
        setToken(token.access_token);
        await loadCurrentUser();
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Login failed.";
        setError(message);
        throw err;
      }
    },
    [loadCurrentUser],
  );

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      setError(null);
      try {
        await api.post<User>("/auth/register", {
          email,
          name,
          password,
        });
        await login(email, password);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Registration failed.";
        setError(message);
        throw err;
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
