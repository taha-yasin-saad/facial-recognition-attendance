import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Employees from "./pages/Employees";
import Enroll from "./pages/Enroll";
import Attendance from "./pages/Attendance";
import Kiosk from "./pages/Kiosk";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminLayout from "./layouts/AdminLayout";
import KioskLayout from "./layouts/KioskLayout";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute>
            <AdminLayout>
              <Routes>
                <Route path="" element={<Dashboard />} />
                <Route path="employees" element={<Employees />} />
                <Route path="enroll/:id" element={<Enroll />} />
                <Route path="attendance" element={<Attendance />} />
              </Routes>
            </AdminLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/kiosk"
        element={
          <KioskLayout>
            <Kiosk />
          </KioskLayout>
        }
      />
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}

export default App;
