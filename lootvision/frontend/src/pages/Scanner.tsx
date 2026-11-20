import { useCallback, useEffect, useState } from "react";
import { CameraFeed } from "../components/CameraFeed";
import { DetectionOverlay } from "../components/DetectionOverlay";
import { ItemDetailSheet } from "../components/ItemDetailSheet";
import { useCamera } from "../hooks/useCamera";
import { useScanLoop } from "../hooks/useScanLoop";
import { getSettings } from "../services/api";
import type { ScanResultItem, UserSettings } from "../types/scan";

const DEFAULT_SETTINGS: UserSettings = {
  currency: "INR",
  marketplace: "mock_catalog",
  default_purchase_price: 0,
  confidence_threshold: 0.65,
  marketplace_fee_percent: 0.1,
  shipping_estimate: 100,
};

export default function Scanner() {
  const { videoRef, status, captureFrame } = useCamera();
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [scanning, setScanning] = useState(true);
  const [selected, setSelected] = useState<ScanResultItem | null>(null);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {
      /* backend not reachable yet — keep client-side defaults */
    });
  }, []);

  const stableCaptureFrame = useCallback(() => captureFrame(), [captureFrame]);

  const { result, error, isScanning } = useScanLoop({
    enabled: scanning && status === "ready",
    captureFrame: stableCaptureFrame,
    settings,
  });

  const items = result?.items ?? [];
  const profitableCount = items.filter((i) => i.pricing?.is_profitable).length;

  return (
    <div className="relative w-full h-[100dvh] pb-16">
      <CameraFeed videoRef={videoRef} status={status} />
      {status === "ready" && (
        <DetectionOverlay items={items} settings={settings} onSelect={setSelected} />
      )}

      {/* top HUD bar */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 pt-[calc(env(safe-area-inset-top)+0.75rem)]">
        <div className="mono text-xs bg-panel/80 border border-line rounded-full px-3 py-1 flex items-center gap-2">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              status === "ready" ? (isScanning ? "bg-scan animate-pulse" : "bg-scan") : "bg-white/30"
            }`}
          />
          {status === "ready" ? (isScanning ? "Scanning…" : "Live") : "Camera off"}
        </div>
        {items.length > 0 && (
          <div className="mono text-xs bg-panel/80 border border-line rounded-full px-3 py-1 text-profit">
            {profitableCount} profitable
          </div>
        )}
      </div>

      {error && (
        <div className="absolute top-16 left-4 right-4 bg-loss/20 border border-loss/40 text-loss text-xs rounded px-3 py-2 mono">
          {error}
        </div>
      )}

      {/* bottom control bar */}
      <div className="absolute bottom-16 left-0 right-0 flex justify-center pb-4">
        <button
          onClick={() => setScanning((s) => !s)}
          className={`mono text-sm px-6 py-2.5 rounded-full border ${
            scanning ? "bg-scan/10 border-scan text-scan" : "bg-panel border-line text-white/60"
          }`}
        >
          {scanning ? "Pause scanning" : "Resume scanning"}
        </button>
      </div>

      {selected && (
        <ItemDetailSheet item={selected} settings={settings} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
