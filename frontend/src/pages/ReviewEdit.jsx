import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";

function ListEditor({ label, items, onChange }) {
  const text = (items || []).join("\n");
  return (
    <div className="form-field">
      <label>{label} <span className="hint">(one per line)</span></label>
      <textarea
        rows={3}
        value={text}
        onChange={(e) => onChange(e.target.value.split("\n").filter((l) => l.trim() !== ""))}
      />
    </div>
  );
}

export default function ReviewEdit() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPatient(patientId)
      .then(setSummary)
      .catch((err) => setError(err.payload?.message || err.message))
      .finally(() => setLoading(false));
  }, [patientId]);

  function update(field, value) {
    setSummary((s) => ({ ...s, [field]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const patch = {
        patient_name: summary.patient_name,
        bed_number: summary.bed_number,
        condition: summary.condition,
        medications: summary.medications,
        vitals: summary.vitals,
        allergies: summary.allergies,
        pending_tasks: summary.pending_tasks,
        observations: summary.observations,
        risk_level: summary.risk_level,
      };
      const updated = await api.updateSummary(patientId, patch);
      setSummary(updated);
    } catch (err) {
      setError(err.payload?.message || "Could not save changes.");
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirm() {
    setSaving(true);
    setError(null);
    try {
      await handleSave();
      const confirmed = await api.confirmSummary(patientId);
      setSummary(confirmed);
    } catch (err) {
      setError(err.payload?.message || "Could not confirm summary.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="page-loading">Loading…</div>;
  if (!summary) return <div className="error-banner">{error}</div>;

  return (
    <div className="page">
      <h1>Review &amp; Confirm Summary</h1>
      <p className="demo-notice">{summary.ai_disclaimer}</p>

      <div className="review-form">
        <div className="form-row">
          <div className="form-field">
            <label>Patient name</label>
            <input value={summary.patient_name || ""} onChange={(e) => update("patient_name", e.target.value)} />
          </div>
          <div className="form-field">
            <label>Bed number</label>
            <input value={summary.bed_number || ""} onChange={(e) => update("bed_number", e.target.value)} />
          </div>
          <div className="form-field">
            <label>Risk level <RiskBadge level={summary.risk_level} /></label>
            <select value={summary.risk_level} onChange={(e) => update("risk_level", e.target.value)}>
              <option>LOW</option>
              <option>MEDIUM</option>
              <option>HIGH</option>
            </select>
          </div>
        </div>

        <div className="form-field">
          <label>Condition</label>
          <textarea rows={2} value={summary.condition || ""} onChange={(e) => update("condition", e.target.value)} />
        </div>

        <ListEditor label="Medications" items={summary.medications} onChange={(v) => update("medications", v)} />
        <ListEditor label="Vitals" items={summary.vitals} onChange={(v) => update("vitals", v)} />
        <ListEditor label="Allergies" items={summary.allergies} onChange={(v) => update("allergies", v)} />
        <ListEditor label="Pending tasks" items={summary.pending_tasks} onChange={(v) => update("pending_tasks", v)} />
        <ListEditor label="Observations" items={summary.observations} onChange={(v) => update("observations", v)} />

        {summary.risk_flags?.length > 0 && (
          <div className="form-field">
            <label>Risk indicators detected (evidence-backed)</label>
            <ul>
              {summary.risk_flags.map((f) => (
                <li key={f.id}>{f.indicator}{f.evidence && ` — "${f.evidence}"`} <em>({f.source})</em></li>
              ))}
            </ul>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div className="review-actions">
          <span className={`review-pill ${summary.review_status === "CONFIRMED" ? "confirmed" : "pending"}`}>
            {summary.review_status === "CONFIRMED" ? "Confirmed" : "Pending review"}
          </span>
          <button onClick={handleSave} disabled={saving}>Save changes</button>
          <button className="primary" onClick={handleConfirm} disabled={saving}>
            Confirm summary
          </button>
          <button onClick={() => navigate(-1)}>Back</button>
        </div>
      </div>
    </div>
  );
}
