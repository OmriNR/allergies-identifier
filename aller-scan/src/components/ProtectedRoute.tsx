import type { ReactNode } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { ROUTES } from "@/lib/app-params";
import { saveReturnTo } from "@/lib/authReturnTo";

const DefaultFallback = () => (
  <div className="fixed inset-0 flex items-center justify-center">
    <div className="w-8 h-8 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin"></div>
  </div>
);

interface ProtectedRouteProps {
  fallback?: ReactNode;
}

export default function ProtectedRoute({
  fallback = <DefaultFallback />,
}: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return fallback;
  }

  if (!user) {
    saveReturnTo(location.pathname + location.search);
    return <Navigate to={ROUTES.login} replace />;
  }

  return <Outlet />;
}
