import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { api, write, token } from "./api";
import type { User } from "../types";
interface Auth {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
const AuthContext = createContext<Auth>(null!);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true);
  function logout() {
    sessionStorage.removeItem("caretrack.token");
    setUser(null);
  }
  useEffect(() => {
    if (token())
      api<User>("/auth/me")
        .then(setUser)
        .catch(logout)
        .finally(() => setLoading(false));
    else setLoading(false);
    window.addEventListener("caretrack:expired", logout);
    return () => window.removeEventListener("caretrack:expired", logout);
  }, []);
  async function login(email: string, password: string) {
    const r = await write<{ access_token: string; user: User }>("/auth/login", {
      email,
      password,
    });
    sessionStorage.setItem("caretrack.token", r.access_token);
    setUser(r.user);
  }
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
