const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
const API_BASE_URL = /^[a-z][a-z\d+.-]*:\/\//i.test(configuredApiUrl)
  ? configuredApiUrl
  : `https://${configuredApiUrl}`;

function getTokens() {
  return {
    access: localStorage.getItem("hm_access_token"),
    refresh: localStorage.getItem("hm_refresh_token"),
  };
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem("hm_access_token", access_token);
  if (refresh_token) localStorage.setItem("hm_refresh_token", refresh_token);
}

export function clearTokens() {
  localStorage.removeItem("hm_access_token");
  localStorage.removeItem("hm_refresh_token");
}

async function request(path, { method = "GET", body, isForm = false, retry = true } = {}) {
  const { access } = getTokens();
  const headers = {};
  if (access) headers["Authorization"] = `Bearer ${access}`;
  if (!isForm && body !== undefined) headers["Content-Type"] = "application/json";

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return request(path, { method, body, isForm, retry: false });
  }

  let data = null;
  try {
    data = await resp.json();
  } catch {
    data = null;
  }

  if (!resp.ok) {
    const err = new Error(data?.message || "Request failed");
    err.status = resp.status;
    err.payload = data;
    throw err;
  }
  return data;
}

async function tryRefresh() {
  const { refresh } = getTokens();
  if (!refresh) return false;
  try {
    const resp = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${refresh}` },
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    setTokens({ access_token: data.access_token });
    return true;
  } catch {
    return false;
  }
}

export const api = {
  login: (email, password) => request("/api/auth/login", { method: "POST", body: { email, password } }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  me: () => request("/api/auth/me"),

  dashboardStats: () => request("/api/dashboard/stats"),

  uploadHandoff: (audioBlob, filename = "handoff.webm") => {
    const form = new FormData();
    form.append("audio", audioBlob, filename);
    return request("/api/handoff/record", { method: "POST", body: form, isForm: true });
  },
  getHandoffSummary: (recordingId) => request(`/api/handoff/${recordingId}/summary`),
  listHandoffs: (page = 1) => request(`/api/handoffs?page=${page}`),

  listPatients: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/patients${qs ? `?${qs}` : ""}`);
  },
  flaggedPatients: () => request("/api/patients/flagged"),
  getPatient: (id) => request(`/api/patients/${id}`),

  updateSummary: (id, patch) => request(`/api/summaries/${id}`, { method: "PATCH", body: patch }),
  confirmSummary: (id) => request(`/api/summaries/${id}/confirm`, { method: "POST" }),

  getJob: (id) => request(`/api/jobs/${id}`),
};

export { API_BASE_URL };
