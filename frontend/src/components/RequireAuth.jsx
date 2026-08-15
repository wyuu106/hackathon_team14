import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/auth-context";

function RequireAuth() {
  const location = useLocation();
  const { authStatus } = useAuth();

  if (authStatus === "loading") return <p>ログイン情報を確認中...</p>;
  return authStatus === "authenticated"
    ? <Outlet />
    : <Navigate to="/login" replace state={{ from: location }} />;
}

export default RequireAuth;
