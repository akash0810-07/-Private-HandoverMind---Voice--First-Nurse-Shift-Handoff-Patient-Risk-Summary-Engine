import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { nurse, loading } = useAuth();

  if (loading) return <div className="page-loading">Loading…</div>;
  if (!nurse) return <Navigate to="/login" replace />;
  if (adminOnly && nurse.role !== "ADMIN") return <Navigate to="/dashboard" replace />;

  return children;
}
