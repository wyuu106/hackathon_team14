import { Navigate, Outlet, useLocation } from "react-router-dom";

function RequireAuth() {
  const location = useLocation();
  return localStorage.getItem("token")
    ? <Outlet />
    : <Navigate to="/login" replace state={{ from: location }} />;
}

export default RequireAuth;
