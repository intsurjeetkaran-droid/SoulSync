/**
 * SoulSync AI - Auth Context
 * Provides user state, login, logout, signup across the app.
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { login as apiLogin, signup as apiSignup, getMe } from "../api/soulsync";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);  // checking stored token

  // ── Restore session from localStorage ─────────────────
  useEffect(() => {
    const token = localStorage.getItem("soulsync_token");
    if (!token) { setLoading(false); return; }

    getMe()
      .then(res => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("soulsync_token");
        localStorage.removeItem("soulsync_user");
      })
      .finally(() => setLoading(false));
  }, []);

  // ── Login ──────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const res  = await apiLogin(email, password);
    const data = res.data;
    localStorage.setItem("soulsync_token", data.access_token);
    localStorage.setItem("soulsync_user",  JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  // ── Signup ─────────────────────────────────────────────
  const signup = useCallback(async (name, email, password) => {
    const res  = await apiSignup(name, email, password);
    const data = res.data;
    localStorage.setItem("soulsync_token", data.access_token);
    localStorage.setItem("soulsync_user",  JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  // ── Update user profile (e.g. after name change via chat) ──
  const updateUser = useCallback((patch) => {
    setUser(prev => {
      if (!prev) return prev;
      const updated = { ...prev, ...patch };
      localStorage.setItem("soulsync_user", JSON.stringify(updated));
      return updated;
    });
  }, []);

  // ── Logout ─────────────────────────────────────────────
  const logout = useCallback(() => {
    localStorage.removeItem("soulsync_token");
    localStorage.removeItem("soulsync_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};
