import React from "react";
import { Navigate } from "react-router-dom";

const tokenKey = "token";

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const token = localStorage.getItem(tokenKey);
  if (!token) {
    return <Navigate to="/login" />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
