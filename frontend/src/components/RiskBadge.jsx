import React from "react";

const COLORS = {
  HIGH: "#b3261e",
  MEDIUM: "#8a5a00",
  LOW: "#1e6b3d",
};

export default function RiskBadge({ level }) {
  const color = COLORS[level] || "#555";
  return (
    <span
      className="risk-badge"
      style={{ backgroundColor: `${color}1a`, color, borderColor: color }}
    >
      {level || "UNKNOWN"}
    </span>
  );
}
