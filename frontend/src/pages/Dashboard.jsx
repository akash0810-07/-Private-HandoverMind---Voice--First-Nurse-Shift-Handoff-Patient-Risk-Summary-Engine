import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";
import PatientCard from "../components/PatientCard.jsx";

function StatCard({ label, value, highlight }) {
  return (
    <div className={`stat-card ${highlight ? "highlight" : ""}`}>
      <span className="stat-value">{value ?? "—"}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [flagged, setFlagged] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.dashboardStats(), api.flaggedPatients()])
      .then(([statsData, flaggedData]) => {
        setStats(statsData);
        setFlagged(flaggedData.items);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading dashboard…</div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="page">
      <h1>Ward Dashboard</h1>

      <div className="stats-grid">
        <StatCard label="Today's handoffs" value={stats.todays_handoffs} />
        <StatCard label="Total patients" value={stats.total_patients} />
        <StatCard label="High risk" value={stats.high_risk_patients} highlight />
        <StatCard label="Medium risk" value={stats.medium_risk_patients} />
        <StatCard label="Low risk" value={stats.low_risk_patients} />
        <StatCard label="Pending reviews" value={stats.pending_reviews} />
        <StatCard label="Confirmed summaries" value={stats.confirmed_summaries} />
      </div>

      <h2>Flagged patients (high &amp; medium risk first)</h2>
      {flagged.length === 0 ? (
        <p className="empty-state">No flagged patients right now.</p>
      ) : (
        <div className="patient-grid">
          {flagged.map((p) => <PatientCard key={p.id} patient={p} />)}
        </div>
      )}
    </div>
  );
}
