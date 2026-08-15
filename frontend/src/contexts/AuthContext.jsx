import { useCallback, useEffect, useMemo, useState } from "react";

import {
  publicApi,
  refreshAccessToken,
  setApiAccessToken,
  setAuthUpdateHandler,
} from "../utils/api";
import { AuthContext } from "./auth-context";

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState("loading");

  const applyAuth = useCallback((authData) => {
    const token = authData?.access_token ?? null;
    setApiAccessToken(token);
    setAccessToken(token);
    setUser(authData?.user ?? null);
    setAuthStatus(authData ? "authenticated" : "unauthenticated");
  }, []);

  useEffect(() => {
    setAuthUpdateHandler(applyAuth);
    refreshAccessToken().catch(() => {});
    return () => setAuthUpdateHandler(() => {});
  }, [applyAuth]);

  const login = useCallback(async (credentials) => {
    const response = await publicApi.post("/login", credentials);
    applyAuth(response.data);
    return response.data.user;
  }, [applyAuth]);

  const logout = useCallback(async () => {
    try {
      await publicApi.post("/auth/logout");
    } finally {
      applyAuth(null);
    }
  }, [applyAuth]);

  const value = useMemo(() => ({
    accessToken,
    user,
    authStatus,
    login,
    logout,
  }), [accessToken, user, authStatus, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
