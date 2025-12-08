// client/src/services/api.js

const API_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function postRoutesJSON(body, opts = {}) {
  const res = await fetch(`${API_BASE}/routes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: opts.signal,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status} - ${txt}`);
  }

  return res.json();
}