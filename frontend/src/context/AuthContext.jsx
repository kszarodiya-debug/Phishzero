import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, authStorage, getApiError } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let active = true;
    const token = authStorage.getToken();
    if (!token) {
      setInitializing(false);
      return () => {
        active = false;
      };
    }

    api.get("/api/auth/me")
      .then(({ data }) => {
        if (active) setUser(data);
      })
      .catch(() => {
        authStorage.clear();
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setInitializing(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setAuthError("Your session expired. Please sign in again.");
    };
    window.addEventListener("phishguard:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("phishguard:unauthorized", handleUnauthorized);
  }, []);

  async function login(email, password) {
    setAuthError("");
    try {
      const { data } = await api.post("/api/auth/login", { email, password });
      authStorage.setToken(data.access_token);
      const profile = await api.get("/api/auth/me");
      setUser(profile.data);
      return profile.data;
    } catch (error) {
      const message = getApiError(error, "Unable to sign in with those credentials.");
      setAuthError(message);
      throw new Error(message);
    }
  }

  async function register(email, password, displayName) {
    setAuthError("");
    try {
      await api.post("/api/auth/register", {
        email,
        password,
        display_name: displayName || undefined,
      });
      return login(email, password);
    } catch (error) {
      const message = getApiError(error, "Unable to create the account.");
      setAuthError(message);
      throw new Error(message);
    }
  }

  function logout() {
    authStorage.clear();
    setUser(null);
    setAuthError("");
  }

  const value = useMemo(
    () => ({ user, initializing, authError, login, register, logout }),
    [user, initializing, authError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
