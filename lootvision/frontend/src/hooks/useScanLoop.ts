import { useEffect, useRef, useState } from "react";
import { scanFrame } from "../services/api";
import type { ScanResponse, UserSettings } from "../types/scan";

interface Options {
  enabled: boolean;
  captureFrame: () => Promise<Blob | null>;
  settings: UserSettings;
  intervalMs?: number;
}

/**
 * Periodically captures a frame and sends it to /api/v1/scan while `enabled`
 * is true. Skips a cycle if the previous request hasn't resolved yet, so a
 * slow backend doesn't queue up a backlog of requests.
 */
export function useScanLoop({ enabled, captureFrame, settings, intervalMs = 1800 }: Options) {
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const inFlight = useRef(false);

  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(async () => {
      if (inFlight.current) return;
      const blob = await captureFrame();
      if (!blob) return;
      inFlight.current = true;
      setIsScanning(true);
      try {
        const res = await scanFrame(blob, {
          purchasePrice: settings.default_purchase_price,
          confidenceThreshold: settings.confidence_threshold,
          feePercent: settings.marketplace_fee_percent,
          shippingEstimate: settings.shipping_estimate,
        });
        setResult(res);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Scan failed");
      } finally {
        inFlight.current = false;
        setIsScanning(false);
      }
    }, intervalMs);
    return () => clearInterval(id);
  }, [enabled, captureFrame, settings, intervalMs]);

  return { result, error, isScanning };
}
