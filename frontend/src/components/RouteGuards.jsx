import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Spinner } from "./common";

export function ProtectedRoute() {
  const { user, initializing } = useAuth();
  const location = useLocation();
  if (initializing) return <div className="flex min-h-screen items-center justify-center bg-slate-950 text-cyan-300"><Spinner label="Loading workspace" /></div>;
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

export function PublicRoute() {
  const { user, initializing } = useAuth();
  if (initializing) return <div className="flex min-h-screen items-center justify-center bg-slate-950 text-cyan-300"><Spinner label="Loading" /></div>;
  return user ? <Navigate to="/dashboard" replace /> : <Outlet />;
}
