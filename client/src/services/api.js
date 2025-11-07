export async function postRoutesJSON(body, opts = {}) {
  const res = await fetch("http://localhost:8000/routes", {
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