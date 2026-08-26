export type HorizonStatus = 'PENDING' | 'COMPLETE' | 'INSUFFICIENT_HORIZON';
export type SessionStatus = 'DRAFT' | 'RUNNING' | 'PAUSED' | 'STOPPED' | 'ABORTED';
export type DriftStatus = 'ALIGNED' | 'MILD_DRIFT' | 'SIGNIFICANT_DRIFT' | 'INSUFFICIENT_SAMPLE';

export interface HorizonOutcome {
  horizon: number;
  status: HorizonStatus;
  target_candle_close_time?: number;
  target_close_price?: number;
  raw_analytical_return?: number;
  cost_adjusted_return_5bps?: number;
  cost_adjusted_return_10bps?: number;
  mfe?: number;
  mae?: number;
  completed_at_timestamp?: number;
}

export interface ShadowSignal {
  signal_id: string;
  session_id: string;
  candidate_id: string;
  symbol: string;
  timeframe: string;
  candle_index: number;
  candle_open_time: number;
  candle_close_time: number;
  entry_reference_price: number;
  direction: string;
  signal_score: number;
  signal_strength: string;
  regime: string;
  structure_state: string;
  volatility_state: string;
  trend_score: number;
  momentum_score: number;
  structure_score: number;
  volume_score: number;
  volatility_score: number;
  regime_score: number;
  vwap_price?: number;
  vwap_distance_atr?: number;
  ema21_price?: number;
  ema21_distance_atr?: number;
  atr: number;
  data_quality_status: string;
  engine_version: string;
  strategy_config_hash: string;
  causal_timestamp: number;
  received_at_timestamp: number;
  processing_latency_ms: number;
  outcomes: Record<number, HorizonOutcome>;
}

export interface CandidateLiveMetrics {
  candidate_id: string;
  candidate_name: string;
  total_signals: number;
  long_count: number;
  short_count: number;
  signals_per_day: number;
  pending_outcomes_count: number;
  completed_outcomes_count: number;
  incomplete_horizons_count: number;
  sample_status: string;
  h1_median_raw: number;
  h3_median_raw: number;
  h5_median_raw: number;
  h10_median_raw: number;
  h20_median_raw: number;
  h5_positive_rate: number;
  h10_positive_rate: number;
  h5_mfe_median: number;
  h5_mae_median: number;
  h5_median_cost_5bps: number;
  h5_median_cost_10bps: number;
  long_5c_median: number;
  short_5c_median: number;
  adjacent_signal_rate: number;
  independent_episodes_count: number;
}

export interface DriftMetricComparison {
  candidate_id: string;
  metric_name: string;
  historical_validation: number;
  historical_test: number;
  live_observed: number;
  drift_delta: number;
  drift_status: DriftStatus;
  details: string;
}

export interface ShadowSession {
  session_id: string;
  symbol: string;
  timeframe: string;
  start_time: number;
  end_time?: number;
  status: SessionStatus;
  final_research_status: string;
  market_data_provider: string;
  configuration_hashes: Record<string, string>;
  last_processed_candle_close_time: number;
  candles_processed_count: number;
  candidates_metrics: Record<string, CandidateLiveMetrics>;
  is_read_only: boolean;
}

export interface ShadowAlert {
  alert_id: string;
  session_id: string;
  timestamp: number;
  alert_type: string;
  candidate_id?: string;
  severity: string;
  title: string;
  message: string;
}
