/**
 * SCALP_STRATEGY_V2 Frontend Type Definitions
 */

export type ScalpV2Direction = 'BUY' | 'SELL' | 'WATCH' | 'NO_TRADE';
export type ScalpV2SetupType = 'TREND_CONTINUATION' | 'PULLBACK' | 'MOMENTUM_BREAKOUT' | 'NONE';
export type ScalpV2TradeState = 'NO_TRADE' | 'WATCH' | 'BUY' | 'SELL';
export type ScalpV2Lifecycle = 'WAITING' | 'ENTRY_READY' | 'ACTIVE' | 'INVALIDATED' | 'EXPIRED';
export type ScalpV2Strength = 'VERY STRONG' | 'STRONG' | 'MODERATE' | 'WEAK' | 'WATCH' | 'NO TRADE';

export interface ScalpV2ScoreFactor {
  name: string;
  timeframe: string;
  score: number;
  max_score: number;
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  detail: string;
}

export interface ScalpV2ScoreBreakdown {
  factors: ScalpV2ScoreFactor[];
  raw_bull_score: number;
  raw_bear_score: number;
  net_score: number;
  normalised_score: number;
  setup_bonus: number;
}

export interface ScalpV2Entry {
  planned_entry: number | null;
  entry_zone_low: number | null;
  entry_zone_high: number | null;
  reference_price: number | null;
}

export interface ScalpV2StopLoss {
  price: number | null;
  risk_distance: number | null;
  risk_distance_atr: number | null;
}

export interface ScalpV2TakeProfits {
  tp1: number | null;
  tp2: number | null;
  tp3: number | null;
  rr_tp1: number | null;
  rr_tp2: number | null;
  rr_tp3: number | null;
}

export interface ScalpV2Signal {
  strategy_id: string;
  strategy_version: string;
  symbol: string;
  primary_timeframe: string;
  direction: ScalpV2Direction;
  trade_state: ScalpV2TradeState;
  lifecycle: ScalpV2Lifecycle;
  setup_type: ScalpV2SetupType;
  score: number;
  alignment_score: number;
  strength: ScalpV2Strength;
  is_preview: boolean;
  candle_timestamp: number;
  calculation_timestamp: number;
  score_breakdown: ScalpV2ScoreBreakdown;
  entry: ScalpV2Entry;
  stop_loss: ScalpV2StopLoss;
  take_profits: ScalpV2TakeProfits;
  supporting_factors: string[];
  conflicting_factors: string[];
  invalidation_conditions: string[];
  context_5m_trend: string;
  context_15m_trend: string;
}

export interface ScalpV2Response {
  confirmed_signal: ScalpV2Signal;
  preview_signal: ScalpV2Signal | null;
  calculation_timestamp: number;
}

export interface ScalpV2HistoryItem {
  timestamp: number;
  direction: ScalpV2Direction;
  score: number;
  alignment_score: number;
  setup_type: ScalpV2SetupType;
  strength: ScalpV2Strength;
  entry_price: number | null;
  stop_loss: number | null;
  tp1: number | null;
  lifecycle: ScalpV2Lifecycle;
}

export interface ScalpV2StatsResponse {
  strategy_id: string;
  symbol: string;
  total_candles_evaluated: number;
  signals_last_hour: number;
  signals_last_4_hours: number;
  signals_last_24_hours: number;
  buy_count: number;
  sell_count: number;
  watch_count: number;
  no_trade_count: number;
  average_score: number;
  average_abs_score: number;
  min_score: number;
  max_score: number;
  setup_distribution: Record<string, number>;
  calculation_timestamp: number;
}

export interface ScalpComparisonResponse {
  symbol: string;
  timeframe: string;
  calculation_timestamp: number;
  v1: {
    strategy_id: string;
    version: string;
    direction: string;
    score: number;
    net_score: number;
    trade_plan: any;
    reasons: string[];
  };
  v2: {
    strategy_id: string;
    version: string;
    direction: string;
    trade_state: string;
    setup_type: string;
    score: number;
    alignment_score: number;
    strength: string;
    entry: any;
    take_profits: any;
    supporting_factors: string[];
    frequency_signals_last_24h: number;
  };
}

export interface HorizonResult {
  horizon_candles: number;
  signals: number;
  tp1_hits: number;
  sl_hits: number;
  ambiguous: number;
  neither: number;
  historical_tp1_hit_rate: number;
}

export interface SetupQualityResult {
  setup_type: string;
  signals: number;
  tp1_hits: number;
  sl_hits: number;
  ambiguous: number;
  neither: number;
  historical_tp1_hit_rate: number;
}

export interface ScoreBucketResult {
  bucket_label: string;
  min_score: number;
  max_score: number;
  signals: number;
  buy_count: number;
  sell_count: number;
  tp1_hits: number;
  sl_hits: number;
  ambiguous: number;
  neither: number;
  historical_tp1_hit_rate: number;
}

export interface SignalFrequencyComparison {
  dataset_duration_hours: number;
  candles_evaluated: number;
  v1_signals: number;
  v1_signals_per_hour: number;
  v2_signals: number;
  v2_signals_per_hour: number;
}

export interface ScalpV2EvaluationReport {
  symbol: string;
  dataset_candles: number;
  candles_evaluated: number;
  dataset_duration_hours: number;
  total_signals: number;
  buy_signals: number;
  sell_signals: number;
  watch_states: number;
  no_trade_states: number;
  frequency_comparison: SignalFrequencyComparison;
  horizon_analysis: HorizonResult[];
  score_breakdown: ScoreBucketResult[];
  setup_breakdown: SetupQualityResult[];
  best_performing_score_bucket: string;
  calculation_timestamp: number;
  disclaimer: string;
}

export interface ScoreBucketDiagnostic {
  bucket_label: string;
  min_score: number;
  max_score: number;
  sample_size_n: number;
  buy_count: number;
  sell_count: number;
  tp1_hit_rate_1c: number;
  tp1_hit_rate_3c: number;
  tp1_hit_rate_5c: number;
  tp1_hit_rate_10c: number;
  tp1_hit_rate_20c: number;
  sl_rate_20c: number;
  neither_rate_20c: number;
  ambiguous_count: number;
  avg_score: number;
  median_score: number;
  is_insufficient_sample: boolean;
}

export interface ScoreMonotonicityReport {
  status: 'MONOTONIC' | 'NON_MONOTONIC' | 'INSUFFICIENT_SAMPLE';
  bucket_hit_rates: Record<string, number>;
  details: string;
  anomaly_detected: boolean;
}

export interface DirectionDiagnostic {
  direction: string;
  sample_size_n: number;
  tp1_hit_rate_1c: number;
  tp1_hit_rate_3c: number;
  tp1_hit_rate_5c: number;
  tp1_hit_rate_10c: number;
  tp1_hit_rate_20c: number;
  sl_rate_20c: number;
  neither_rate_20c: number;
  avg_score: number;
  avg_abs_score: number;
  is_insufficient_sample: boolean;
}

export interface SetupDiagnostic {
  setup_type: string;
  sample_size_n: number;
  buy_count: number;
  sell_count: number;
  tp1_hit_rate_1c: number;
  tp1_hit_rate_3c: number;
  tp1_hit_rate_5c: number;
  tp1_hit_rate_10c: number;
  tp1_hit_rate_20c: number;
  sl_rate_20c: number;
  neither_rate_20c: number;
  avg_score: number;
  is_insufficient_sample: boolean;
  diagnostic_notes: string;
}

export interface TimingDistribution {
  tp1_before_sl_count: number;
  sl_before_tp1_count: number;
  neither_count: number;
  ambiguous_count: number;
  tp1_within_1c: number;
  tp1_within_2c: number;
  tp1_within_3c: number;
  tp1_within_5c: number;
  tp1_within_10c: number;
  tp1_within_20c: number;
  avg_candles_to_tp1: number | null;
  median_candles_to_tp1: number | null;
  avg_candles_to_sl: number | null;
  median_candles_to_sl: number | null;
}

export interface EntryTimingDiagnostic {
  timely_count: number;
  early_count: number;
  late_count: number;
  undetermined_count: number;
  notes: string;
}

export interface FactorDiagnostic {
  factor_name: string;
  avg_contribution: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  tp1_hit_rate_strongly_positive: number | null;
  strongly_pos_n: number;
  tp1_hit_rate_neutral: number | null;
  neutral_n: number;
  tp1_hit_rate_strongly_negative: number | null;
  strongly_neg_n: number;
}

export interface ClusteringDiagnostic {
  signals_per_hour: number;
  signals_per_4h: number;
  avg_time_between_signals_min: number;
  median_time_between_signals_min: number;
  max_signals_in_rolling_5m: number;
  max_signals_in_rolling_15m: number;
  same_direction_clusters_count: number;
}

export interface FlipDiagnostic {
  flips_total: number;
  flips_per_hour: number;
  avg_score_before_flip: number;
  avg_score_after_flip: number;
  min_minutes_between_flips: number | null;
}

export interface SetupAccountingReport {
  total_signals: number;
  trend_continuation_count: number;
  pullback_count: number;
  momentum_breakout_count: number;
  unclassified_count: number;
  unclassified_reasons: Record<string, number>;
  reconciliation_valid: boolean;
}

export interface ScalpV2DiagnosticReport {
  symbol: string;
  dataset_candles: number;
  candles_evaluated: number;
  dataset_duration_hours: number;
  total_signals: number;
  classified_signals: number;
  unclassified_signals: number;
  setup_accounting: SetupAccountingReport;
  score_analysis: ScoreBucketDiagnostic[];
  score_monotonicity: ScoreMonotonicityReport;
  direction_analysis: Record<string, DirectionDiagnostic>;
  setup_analysis: SetupDiagnostic[];
  timing_analysis: TimingDistribution;
  entry_timing: EntryTimingDiagnostic;
  factor_analysis: FactorDiagnostic[];
  clustering_analysis: ClusteringDiagnostic;
  flip_analysis: FlipDiagnostic;
  warnings: string[];
  recommended_next_investigation: string[];
  calculation_timestamp: number;
  disclaimer: string;
}
