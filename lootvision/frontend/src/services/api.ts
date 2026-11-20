import type { ScanHistoryEntry, ScanResponse, UserSettings } from "../types/scan";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function scanFrame(
  blob: Blob,
  opts: { purchasePrice: number; confidenceThreshold: number; feePercent: number; shippingEstimate: number }
): Promise<ScanResponse> {
  const form = new FormData();
  form.append("file", blob, "frame.jpg");
  form.append("purchase_price", String(opts.purchasePrice));
  form.append("confidence_threshold", String(opts.confidenceThreshold));
  form.append("fee_percent", String(opts.feePercent));
  form.append("shipping_estimate", String(opts.shippingEstimate));

  const res = await fetch(`${API_BASE}/api/v1/scan`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Scan failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function getHistory(limit = 50): Promise<ScanHistoryEntry[]> {
  const res = await fetch(`${API_BASE}/api/v1/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`);
  return res.json();
}

export async function getSettings(): Promise<UserSettings> {
  const res = await fetch(`${API_BASE}/api/v1/settings`);
  if (!res.ok) throw new Error(`Failed to load settings: ${res.status}`);
  return res.json();
}

export async function updateSettings(settings: UserSettings): Promise<UserSettings> {
  const res = await fetch(`${API_BASE}/api/v1/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(`Failed to save settings: ${res.status}`);
  return res.json();
}
