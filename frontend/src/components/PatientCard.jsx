import React from "react";
import { Link } from "react-router-dom";
import RiskBadge from "./RiskBadge.jsx";

function ListField({ label, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <ul>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  );
}

export default function PatientCard({ patient }) {
  return (
    <div className={`patient-card risk-${patient.risk_level?.toLowerCase()}`}>
      <div className="patient-card-header">
        <div>
          <strong>{patient.patient_name || "Unnamed patient"}</strong>
          {patient.bed_number && <span className="bed-tag">Bed {patient.bed_number}</span>}
        </div>
        <RiskBadge level={patient.risk_level} />
      </div>

      {patient.condition && <p className="condition">{patient.condition}</p>}

      <ListField label="Medications" items={patient.medications} />
      <ListField label="Vitals" items={patient.vitals} />
      <ListField label="Allergies" items={patient.allergies} />
      <ListField label="Pending tasks" items={patient.pending_tasks} />
      <ListField label="Observations" items={patient.observations} />

      {patient.risk_flags?.length > 0 && (
        <div className="field risk-flags">
          <span className="field-label">Risk indicators</span>
          <ul>
            {patient.risk_flags.map((f) => (
              <li key={f.id}>
                {f.indicator}
                {f.evidence && <em className="evidence"> — "{f.evidence}"</em>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="patient-card-footer">
        <span className={`review-pill ${patient.review_status === "CONFIRMED" ? "confirmed" : "pending"}`}>
          {patient.review_status === "CONFIRMED" ? "Confirmed" : "Pending review"}
        </span>
        <span className="confidence">AI confidence: {(patient.ai_confidence * 100).toFixed(0)}%</span>
        <Link to={`/review/${patient.id}`} className="review-link">Review / Edit</Link>
      </div>
      <p className="ai-disclaimer">{patient.ai_disclaimer}</p>
    </div>
  );
}
