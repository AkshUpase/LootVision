import { useEffect, useState } from "react";
import { getHistory } from "../services/api";
import type { ScanHistoryEntry } from "../types/scan";

export default function History() {
  const [entries, setEntries] = useState<ScanHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    getHistory()
      .then(setEntries)
      .catch(() => setErrored(true))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-[100dvh] pb-20 px-4 pt-[calc(env(safe-area-inset-top)+1.25rem)]">
      <h1 className="text-xl font-semibold mb-4">Scan History</h1>

      {loading && <p className="text-white/40 mono text-sm">Loading…</p>}
      {errored && (
        <p className="text-loss mono text-sm">Couldn't reach the backend. Is it running on :8000?</p>
      )}
      {!loading && !errored && entries.length === 0 && (
        <p className="text-white/40 text-sm">No scans yet — matched items will show up here.</p>
      )}

      <div className="space-y-2">
        {entries.map((e) => (
          <div
            key={e.scan_id}
            className="flex items-center justify-between bg-panel border border-line rounded-lg px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium">{e.product_name}</p>
              <p className="text-xs text-white/40 mono">
                {new Date(e.timestamp).toLocaleString()} · condition {e.condition_score}/100
              </p>
            </div>
            <span
              className={`mono text-sm font-semibold ${e.estimated_profit >= 0 ? "text-profit" : "text-loss"}`}
            >
              {e.estimated_profit >= 0 ? "+" : ""}
              {Math.round(e.estimated_profit).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
