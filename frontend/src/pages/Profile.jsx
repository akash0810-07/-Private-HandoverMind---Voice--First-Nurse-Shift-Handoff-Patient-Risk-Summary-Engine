import React from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Profile() {
  const { nurse } = useAuth();
  if (!nurse) return null;

  return (
    <div className="page">
      <h1>Profile</h1>
      <div className="profile-card">
        <p><strong>Name:</strong> {nurse.full_name}</p>
        <p><strong>Email:</strong> {nurse.email}</p>
        <p><strong>Role:</strong> {nurse.role}</p>
        <p><strong>Ward:</strong> {nurse.ward_name || "Not assigned"}</p>
      </div>
      <p className="demo-notice">Academic demonstration system — uses synthetic patient data only.</p>
    </div>
  );
}
