// SCALP_STRATEGY_V1 TypeScript types — independent of Phase 5 / Phase 10 types

export type ScalpDirection = 'BUY' | 'SELL' | 'NO_TRADE';

export interface ScalpScoreFactor {
  name: string;
  timeframe: string;
  score: number;
  max_score: number;
  direction: string;
  detail: string;
}

export interface ScalpScoreBreakdown {
  factors: ScalpScoreFactor[];
  raw_bull_score: number;
  raw_bear_score: number;
  net_score: number;
  normalised_score: number;
}

export interface ScalpTradePlan {
  entry_price: number | null;
  stop_loss: number | null;
  tp1: number | null;
  tp2: number | null;
  tp3: number | null;
  rr_tp1: number | null;
  rr_tp2: number | null;
  rr_tp3: number | null;
  atr_used: number | null;
  plan_available: boolean;
  plan_rejection_reason: string | null;
}

export interface ScalpSignal {
  strategy_id: string;
  strategy_version: string;
  symbol: string;
  primary_timeframe: string;
  direction: ScalpDirection;
  score_breakdown: ScalpScoreBreakdown;
  trade_plan: ScalpTradePlan;
  is_preview: boolean;
  candle_timestamp: number;
  calculation_timestamp: number;
  reasons: string[];
  invalidation_conditions: string[];
  context_5m_trend: string;
  context_15m_trend: string;
  phase5_research_direction: string;
}

export interface ScalpResponse {
  confirmed_signal: ScalpSignal;
  preview_signal: ScalpSignal | null;
  calculation_timestamp: number;
}
