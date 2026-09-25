import React, { createContext, useContext, useEffect, useState } from "react";
import { api, setTokens, clearTokens } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [nurse, setNurse] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("hm_access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.me()
      .then(setNurse)
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const data = await api.login(email, password);
    setTokens(data);
    setNurse(data.nurse);
    return data.nurse;
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      // ignore network errors on logout
    }
    clearTokens();
    setNurse(null);
  }

  return (
    <AuthContext.Provider value={{ nurse, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
