import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { nurse, logout } = useAuth();
  const navigate = useNavigate();

  if (!nurse) return null;

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <Link to="/dashboard">HandoverMind</Link>
        <span className="demo-badge">Synthetic data only</span>
      </div>
      <nav>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/record">Start Handoff</Link>
        <Link to="/history">History</Link>
        <Link to="/profile">Profile</Link>
        {nurse.role === "ADMIN" && <Link to="/admin">Admin</Link>}
      </nav>
      <div className="navbar-user">
        <span>{nurse.full_name} · {nurse.ward_name || "No ward"}</span>
        <button onClick={handleLogout}>Log out</button>
      </div>
    </header>
  );
}
