import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import StartHandoff from "./pages/StartHandoff.jsx";
import HandoffSummary from "./pages/HandoffSummary.jsx";
import ReviewEdit from "./pages/ReviewEdit.jsx";
import HandoffHistory from "./pages/HandoffHistory.jsx";
import Profile from "./pages/Profile.jsx";
import Admin from "./pages/Admin.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/record" element={<ProtectedRoute><StartHandoff /></ProtectedRoute>} />
          <Route path="/summary/:recordingId" element={<ProtectedRoute><HandoffSummary /></ProtectedRoute>} />
          <Route path="/review/:patientId" element={<ProtectedRoute><ReviewEdit /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><HandoffHistory /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute adminOnly><Admin /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}
