import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "../services/api";
import type { UserSettings } from "../types/scan";

const DEFAULTS: UserSettings = {
  currency: "INR",
  marketplace: "mock_catalog",
  default_purchase_price: 0,
  confidence_threshold: 0.65,
  marketplace_fee_percent: 0.1,
  shipping_estimate: 100,
};

export default function Settings() {
  const [settings, setSettings] = useState<UserSettings>(DEFAULTS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
  }, []);

  async function save() {
    await updateSettings(settings).catch(() => {});
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div className="min-h-[100dvh] pb-20 px-4 pt-[calc(env(safe-area-inset-top)+1.25rem)]">
      <h1 className="text-xl font-semibold mb-4">Settings</h1>

      <div className="space-y-5">
        <Field label="Currency">
          <select
            value={settings.currency}
            onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
            className="bg-void border border-line rounded px-3 py-2 w-full mono text-sm"
          >
            {["INR", "USD", "EUR", "GBP"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </Field>

        <Field label="Marketplace / price source">
          <select
            value={settings.marketplace}
            onChange={(e) => setSettings({ ...settings, marketplace: e.target.value })}
            className="bg-void border border-line rounded px-3 py-2 w-full mono text-sm"
          >
            <option value="mock_catalog">Mock catalog (demo data)</option>
            <option value="ebay_browse_api">eBay Browse API (requires backend key)</option>
          </select>
        </Field>

        <Field label={`Default purchase price (${settings.currency})`}>
          <input
            type="number"
            value={settings.default_purchase_price}
            onChange={(e) => setSettings({ ...settings, default_purchase_price: Number(e.target.value) })}
            className="bg-void border border-line rounded px-3 py-2 w-full mono text-sm"
          />
        </Field>

        <Field label={`Confidence threshold — ${Math.round(settings.confidence_threshold * 100)}%`}>
          <input
            type="range"
            min={0.3}
            max={0.95}
            step={0.05}
            value={settings.confidence_threshold}
            onChange={(e) => setSettings({ ...settings, confidence_threshold: Number(e.target.value) })}
            className="w-full accent-scan"
          />
        </Field>

        <Field label={`Marketplace fee — ${Math.round(settings.marketplace_fee_percent * 100)}%`}>
          <input
            type="range"
            min={0}
            max={0.3}
            step={0.01}
            value={settings.marketplace_fee_percent}
            onChange={(e) => setSettings({ ...settings, marketplace_fee_percent: Number(e.target.value) })}
            className="w-full accent-scan"
          />
        </Field>

        <Field label={`Shipping estimate (${settings.currency})`}>
          <input
            type="number"
            value={settings.shipping_estimate}
            onChange={(e) => setSettings({ ...settings, shipping_estimate: Number(e.target.value) })}
            className="bg-void border border-line rounded px-3 py-2 w-full mono text-sm"
          />
        </Field>

        <button
          onClick={save}
          className="w-full mono text-sm bg-scan/10 border border-scan text-scan rounded-lg py-2.5 mt-2"
        >
          {saved ? "Saved" : "Save settings"}
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-wide text-white/40 mb-1.5">{label}</label>
      {children}
    </div>
  );
}
