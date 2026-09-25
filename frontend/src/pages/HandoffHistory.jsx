import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

export default function HandoffHistory() {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listHandoffs(page).then(setData).catch((err) => setError(err.message));
  }, [page]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <div className="page-loading">Loading history…</div>;

  return (
    <div className="page">
      <h1>Handoff History</h1>
      <table className="history-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Recorded by</th>
            <th>Status</th>
            <th>Patients</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((h) => (
            <tr key={h.id}>
              <td>{new Date(h.created_at).toLocaleString()}</td>
              <td>{h.recorded_by}</td>
              <td>{h.status}</td>
              <td><Link to={`/summary/${h.id}`}>View summary</Link></td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
        <span>Page {data.page} of {data.pages || 1}</span>
        <button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </div>
  );
}
