/**
 * Phase 10 — Trade Decision Engine TypeScript Type Definitions.
 * Analytical trade decision, entry zones, structural stops, and take profit plans.
 */

export type TradeDecisionType = "BUY" | "SELL" | "NO_TRADE";

export type TradePlanState =
  | "NO_TRADE"
  | "WAITING_FOR_ENTRY"
  | "ENTRY_ZONE_ACTIVE"
  | "INVALIDATED"
  | "EXPIRED";

export type DecisionStatusType = "VALID" | "WAITING" | "INVALID";

export type EntryType =
  | "PULLBACK_ZONE"
  | "BREAKOUT_REFERENCE"
  | "MARKET_REFERENCE"
  | "NO_ENTRY";

export type ConfidenceGrade = "VERY_HIGH" | "HIGH" | "MODERATE" | "LOW" | "VERY_LOW";

export type AuditCheckStatus = "PASS" | "FAIL" | "NOT_APPLICABLE";

export interface AuditCheckItem {
  check_name: string;
  status: AuditCheckStatus;
  reason: string;
  details?: Record<string, any>;
}

export interface DecisionAuditTrace {
  data_quality_check: AuditCheckItem;
  signal_check: AuditCheckItem;
  strategy_filter_check: AuditCheckItem;
  regime_check: AuditCheckItem;
  structure_check: AuditCheckItem;
  sr_clearance_check: AuditCheckItem;
  entry_check: AuditCheckItem;
  stop_check: AuditCheckItem;
  target_check: AuditCheckItem;
  risk_reward_check: AuditCheckItem;
  confidence_check: AuditCheckItem;
  final_decision: AuditCheckItem;
}

export interface EntryPlan {
  reference_price: number;
  planned_entry_price: number;
  entry_type: EntryType;
  entry_zone_low: number;
  entry_zone_high: number;
  formula_description: string;
}

export interface StopLossPlan {
  price: number;
  distance: number;
  distance_atr: number;
  reason: string;
  structural_reference_level?: number | null;
  atr_buffer_used: number;
}

export interface TargetLevelDetail {
  original_target: number;
  adjusted_target: number;
  structural_level?: number | null;
  adjustment_reason: string;
  r_multiple_base: number;
  actual_rr_after_adjustment: number;
  distance: number;
  constrained_by_structure: boolean;
}

export interface TakeProfitPlan {
  tp1: TargetLevelDetail;
  tp2: TargetLevelDetail;
  tp3: TargetLevelDetail;
}

export interface RiskRewardSummary {
  tp1_rr: number;
  tp2_rr: number;
  tp3_rr: number;
  is_acceptable: boolean;
  rejection_reason?: string | null;
}

export interface DecisionContext {
  signal_score: number;
  regime: string;
  trend_strength: string;
  structure: string;
  volatility: string;
  momentum: string;
  volume: string;
}

export interface TradePlan {
  decision: TradeDecisionType;
  direction: "LONG" | "SHORT" | "NEUTRAL";
  state: TradePlanState;
  status: DecisionStatusType;
  decision_alignment_score: number;
  confidence_grade: ConfidenceGrade;
  strategy_context_id: string;
  strategy_context_version: string;
  strategy_config_hash: string;
  symbol: string;
  timeframe: string;
  decision_candle_open_time: number;
  decision_candle_close_time: number;
  calculated_at: number;
  market_data_last_updated_at: number;
  created_at: number;
  valid_until: number;
  max_valid_candles: number;
  bars_since_creation: number;
  is_confirmed: boolean;
  is_preview: boolean;
  entry?: EntryPlan | null;
  stop_loss?: StopLossPlan | null;
  take_profits?: TakeProfitPlan | null;
  risk_reward?: RiskRewardSummary | null;
  context: DecisionContext;
  supporting_factors: string[];
  conflicting_factors: string[];
  reasons_for_no_trade: string[];
  invalidation_conditions: string[];
  audit_trace: DecisionAuditTrace;
  decision_engine_version: string;
  decision_config_version: string;
}

export interface MultiStrategyTradeDecisions {
  symbol: string;
  timeframe: string;
  timestamp: number;
  is_confirmed: boolean;
  selected_strategy_id: string;
  primary_decision: TradePlan;
  candidate_decisions: Record<string, TradePlan>;
}
