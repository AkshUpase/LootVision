// Mirrors backend/models/schemas.py — keep these in sync manually, or
// generate from the FastAPI OpenAPI schema later (openapi-typescript).

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectedObject {
  detection_id: string;
  bbox: BoundingBox;
  category: string;
  detection_confidence: number;
}

export interface ProductMatch {
  product_id: string;
  product_name: string;
  brand: string | null;
  category: string;
  image_url: string | null;
  similarity: number;
  marketplace_price: number;
  source: string;
}

export interface ConditionAssessment {
  score: number;
  label: "Poor" | "Fair" | "Good" | "Excellent";
  visible_damage: string[];
  method: "baseline_heuristic" | "trained_model";
  note: string;
}

export interface MatchConfidence {
  level: "low" | "medium" | "high" | "none";
  threshold_used: number;
}

export interface PricingBreakdown {
  estimated_resale_price: number;
  condition_adjustment: number;
  estimated_fees: number;
  purchase_price: number;
  estimated_profit: number;
  roi_percent: number;
  is_profitable: boolean;
  price_source: "mock" | "ebay_browse_api";
  disclaimer: string;
}

export interface ScanResultItem {
  detection: DetectedObject;
  best_match: ProductMatch | null;
  alternatives: ProductMatch[];
  condition: ConditionAssessment | null;
  pricing: PricingBreakdown | null;
  confidence: MatchConfidence;
}

export interface ScanResponse {
  scan_id: string;
  timestamp: string;
  items: ScanResultItem[];
  processing_time_ms: number;
}

export interface ScanHistoryEntry {
  scan_id: string;
  timestamp: string;
  product_name: string;
  estimated_profit: number;
  condition_score: number;
  thumbnail_url: string | null;
}

export interface UserSettings {
  currency: string;
  marketplace: string;
  default_purchase_price: number;
  confidence_threshold: number;
  marketplace_fee_percent: number;
  shipping_estimate: number;
}
