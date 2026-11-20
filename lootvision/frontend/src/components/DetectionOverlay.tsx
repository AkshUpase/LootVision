import type { ScanResultItem, UserSettings } from "../types/scan";

interface Props {
  items: ScanResultItem[];
  settings: UserSettings;
  onSelect: (item: ScanResultItem) => void;
}

const CURRENCY_SYMBOL: Record<string, string> = { INR: "₹", USD: "$", EUR: "€", GBP: "£" };

function formatMoney(value: number, currency: string) {
  const symbol = CURRENCY_SYMBOL[currency] ?? currency + " ";
  return `${symbol}${Math.round(value).toLocaleString()}`;
}

function confidenceColor(level: string) {
  if (level === "high") return "border-scan text-scan";
  if (level === "medium") return "border-signal text-signal";
  if (level === "low") return "border-white/40 text-white/60";
  return "border-loss/60 text-loss";
}

export function DetectionOverlay({ items, settings, onSelect }: Props) {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {items.map((item) => {
        const { bbox } = item.detection;
        const boxColor = confidenceColor(item.confidence.level);
        const left = `${bbox.x * 100}%`;
        const top = `${bbox.y * 100}%`;
        const width = `${bbox.width * 100}%`;
        const height = `${bbox.height * 100}%`;

        return (
          <div
            key={item.detection.detection_id}
            className={`detection-box absolute border-2 rounded-md ${boxColor} pointer-events-auto`}
            style={{ left, top, width, height }}
            onClick={() => onSelect(item)}
          >
            {/* corner ticks for a HUD feel instead of a plain rectangle */}
            <span className="absolute -top-[2px] -left-[2px] w-3 h-3 border-t-2 border-l-2 border-current" />
            <span className="absolute -top-[2px] -right-[2px] w-3 h-3 border-t-2 border-r-2 border-current" />
            <span className="absolute -bottom-[2px] -left-[2px] w-3 h-3 border-b-2 border-l-2 border-current" />
            <span className="absolute -bottom-[2px] -right-[2px] w-3 h-3 border-b-2 border-r-2 border-current" />

            <div className="absolute left-0 -top-7 max-w-[220px]">
              {item.confidence.level === "none" ? (
                <div className="mono text-[11px] bg-panel/95 border border-line rounded px-2 py-1 text-white/60 whitespace-nowrap">
                  No reliable match — try another angle
                </div>
              ) : (
                <div className="mono text-[11px] bg-panel/95 border border-line rounded px-2 py-1 whitespace-nowrap">
                  <span className={confidenceColor(item.confidence.level).split(" ")[1]}>
                    {item.best_match?.product_name ?? item.detection.category}
                  </span>
                  <span className="text-white/40"> · {Math.round(item.best_match!.similarity * 100)}%</span>
                </div>
              )}
            </div>

            {item.pricing && (
              <div className="absolute left-0 top-full mt-1 bg-panel/95 border border-line rounded-lg px-3 py-2 shadow-glow min-w-[160px]">
                <div className="flex justify-between items-baseline gap-3">
                  <span className="text-signal font-semibold mono text-sm">
                    {formatMoney(item.pricing.estimated_resale_price, settings.currency)}
                  </span>
                  <span className="text-[10px] text-white/40 uppercase tracking-wide">resale</span>
                </div>
                <div className="flex justify-between items-baseline gap-3 mt-0.5">
                  <span
                    className={`font-semibold mono text-sm ${item.pricing.is_profitable ? "text-profit" : "text-loss"}`}
                  >
                    {item.pricing.estimated_profit >= 0 ? "+" : ""}
                    {formatMoney(item.pricing.estimated_profit, settings.currency)}
                  </span>
                  <span
                    className={`text-[10px] uppercase tracking-wide font-semibold ${
                      item.pricing.is_profitable ? "text-profit" : "text-loss"
                    }`}
                  >
                    {item.pricing.is_profitable ? "Profitable" : "Skip"}
                  </span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
