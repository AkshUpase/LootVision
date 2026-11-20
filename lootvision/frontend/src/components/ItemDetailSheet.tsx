import type { ScanResultItem, UserSettings } from "../types/scan";

interface Props {
  item: ScanResultItem;
  settings: UserSettings;
  onClose: () => void;
}

const CURRENCY_SYMBOL: Record<string, string> = { INR: "₹", USD: "$", EUR: "€", GBP: "£" };
function fmt(v: number, currency: string) {
  return `${CURRENCY_SYMBOL[currency] ?? currency + " "}${Math.round(v).toLocaleString()}`;
}

export function ItemDetailSheet({ item, settings, onClose }: Props) {
  const match = item.best_match;

  return (
    <div className="fixed inset-0 z-30 flex items-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70" />
      <div
        className="relative w-full bg-panel border-t border-line rounded-t-2xl p-5 pb-[calc(env(safe-area-inset-bottom)+1.5rem)] max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-10 h-1 bg-white/20 rounded-full mx-auto mb-4" />

        {!match ? (
          <div className="text-center py-8">
            <p className="text-white/70 mono text-sm">No reliable match found.</p>
            <p className="text-white/40 text-xs mt-1">Try moving closer or changing the angle.</p>
          </div>
        ) : (
          <>
            <div className="flex justify-between items-start gap-4">
              <div>
                <h2 className="text-lg font-semibold">{match.product_name}</h2>
                {match.brand && <p className="text-white/50 text-sm">{match.brand}</p>}
              </div>
              <span className="mono text-xs bg-line rounded px-2 py-1 text-scan whitespace-nowrap">
                {Math.round(match.similarity * 100)}% match
              </span>
            </div>

            {item.condition && (
              <div className="mt-4 bg-void/60 border border-line rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Condition: {item.condition.label}</span>
                  <span className="mono text-sm text-signal">{item.condition.score}/100</span>
                </div>
                <ul className="mt-2 space-y-1">
                  {item.condition.visible_damage.map((d, i) => (
                    <li key={i} className="text-xs text-white/50">• {d}</li>
                  ))}
                </ul>
                <p className="text-[11px] text-white/30 mt-2">{item.condition.note}</p>
              </div>
            )}

            {item.pricing && (
              <div className="mt-4 space-y-2">
                <Row label="Estimated resale" value={fmt(item.pricing.estimated_resale_price, settings.currency)} />
                <Row
                  label="Condition adjustment"
                  value={fmt(item.pricing.condition_adjustment, settings.currency)}
                  muted
                />
                <Row label="Estimated fees" value={`-${fmt(item.pricing.estimated_fees, settings.currency)}`} muted />
                <Row label="Purchase price" value={fmt(item.pricing.purchase_price, settings.currency)} muted />
                <div className="border-t border-line pt-2 flex justify-between items-baseline">
                  <span className="text-sm font-medium">Estimated profit</span>
                  <span
                    className={`mono text-base font-semibold ${
                      item.pricing.is_profitable ? "text-profit" : "text-loss"
                    }`}
                  >
                    {fmt(item.pricing.estimated_profit, settings.currency)} ({item.pricing.roi_percent}% ROI)
                  </span>
                </div>
                <p className="text-[11px] text-white/30">
                  {item.pricing.price_source === "mock"
                    ? "Pricing is sample/demo data, not a live marketplace price."
                    : "Pricing sourced from eBay Browse API listings."}
                </p>
              </div>
            )}

            {item.alternatives.length > 0 && (
              <div className="mt-4">
                <p className="text-xs uppercase tracking-wide text-white/40 mb-2">Other possible matches</p>
                <div className="space-y-1">
                  {item.alternatives.map((alt) => (
                    <div key={alt.product_id} className="flex justify-between text-sm text-white/60">
                      <span>{alt.product_name}</span>
                      <span className="mono text-xs">{Math.round(alt.similarity * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, muted }: { label: string; value: string; muted?: boolean }) {
  return (
    <div className="flex justify-between text-sm">
      <span className={muted ? "text-white/40" : ""}>{label}</span>
      <span className={`mono ${muted ? "text-white/40" : ""}`}>{value}</span>
    </div>
  );
}
