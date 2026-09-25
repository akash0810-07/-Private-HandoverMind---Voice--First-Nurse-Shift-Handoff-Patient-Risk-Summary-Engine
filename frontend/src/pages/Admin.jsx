import React, { useEffect, useState } from "react";
import { API_BASE_URL } from "../api/client.js";

async function authedFetch(path, opts = {}) {
  const token = localStorage.getItem("hm_access_token");
  const resp = await fetch(`${API_BASE_URL}${path}`, {
    ...opts,
    headers: { ...(opts.headers || {}), Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  return resp.json();
}

export default function Admin() {
  const [wards, setWards] = useState([]);
  const [nurses, setNurses] = useState([]);
  const [newWard, setNewWard] = useState("");

  function refresh() {
    authedFetch("/api/admin/wards").then((d) => setWards(d.items || []));
    authedFetch("/api/admin/nurses").then((d) => setNurses(d.items || []));
  }

  useEffect(refresh, []);

  async function createWard(e) {
    e.preventDefault();
    if (!newWard.trim()) return;
    await authedFetch("/api/admin/wards", { method: "POST", body: JSON.stringify({ name: newWard }) });
    setNewWard("");
    refresh();
  }

  async function assignWard(nurseId, wardId) {
    await authedFetch(`/api/admin/nurses/${nurseId}/ward`, {
      method: "PATCH", body: JSON.stringify({ ward_id: wardId }),
    });
    refresh();
  }

  return (
    <div className="page">
      <h1>Ward &amp; Nurse Administration</h1>

      <section>
        <h2>Wards</h2>
        <ul>{wards.map((w) => <li key={w.id}>{w.name}</li>)}</ul>
        <form onSubmit={createWard} className="inline-form">
          <input placeholder="New ward name" value={newWard} onChange={(e) => setNewWard(e.target.value)} />
          <button type="submit">Add ward</button>
        </form>
      </section>

      <section>
        <h2>Nurses</h2>
        <table className="history-table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Ward</th></tr></thead>
          <tbody>
            {nurses.map((n) => (
              <tr key={n.id}>
                <td>{n.full_name}</td>
                <td>{n.email}</td>
                <td>{n.role}</td>
                <td>
                  <select value={n.ward_id || ""} onChange={(e) => assignWard(n.id, e.target.value)}>
                    <option value="">Unassigned</option>
                    {wards.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
