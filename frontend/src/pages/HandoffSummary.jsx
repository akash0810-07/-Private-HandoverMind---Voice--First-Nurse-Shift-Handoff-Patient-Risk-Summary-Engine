import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client.js";
import PatientCard from "../components/PatientCard.jsx";

export default function HandoffSummary() {
  const { recordingId } = useParams();
  const [recording, setRecording] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHandoffSummary(recordingId)
      .then(setRecording)
      .catch((err) => setError(err.payload?.message || err.message))
      .finally(() => setLoading(false));
  }, [recordingId]);

  if (loading) return <div className="page-loading">Loading summary…</div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="page">
      <h1>AI Summary Ready for Review</h1>
      <p className="demo-notice">
        AI-generated summary — review and confirm before use. This tool assists documentation
        only and does not diagnose or recommend treatment.
      </p>

      <details className="transcript-box">
        <summary>View raw transcript</summary>
        <p>{recording.transcript}</p>
      </details>

      <div className="patient-grid">
        {recording.patient_summaries.map((p) => <PatientCard key={p.id} patient={p} />)}
      </div>

      <Link to="/dashboard" className="back-link">Back to dashboard</Link>
    </div>
  );
}
