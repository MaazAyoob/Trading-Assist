export type OutcomeClassification =
  | 'POSITIVE_FORWARD_RETURN'
  | 'NEGATIVE_FORWARD_RETURN'
  | 'FLAT_FORWARD_RETURN'
  | 'INSUFFICIENT_HORIZON';

export interface HorizonOutcome {
  horizon: number;
  future_close?: number;
  forward_return?: number;
  mfe?: number;
  mae?: number;
  status: OutcomeClassification;
  estimated_net_forward_return?: number;
}

export interface SignalOutcome {
  signal_id: string;
  symbol: string;
  timeframe: string;
  signal_timestamp: number;
  signal_direction: 'LONG_SETUP' | 'SHORT_SETUP';
  signal_strength: string;
  signal_score: number;
  entry_reference_price: number;
  outcomes: Record<number, HorizonOutcome>;
  regime_at_signal: string;
  structure_at_signal: string;
  volatility_at_signal: string;
  engine_version: string;
  config_version: string;
}

export interface DistributionStats {
  sample_count: number;
  mean?: number;
  median?: number;
  std_dev?: number;
  std_error?: number;
  ci_lower_normal?: number;
  ci_upper_normal?: number;
  bootstrap_mean_ci_lower?: number;
  bootstrap_mean_ci_upper?: number;
  bootstrap_median_ci_lower?: number;
  bootstrap_median_ci_upper?: number;
  p5?: number;
  p25?: number;
  p50?: number;
  p75?: number;
  p95?: number;
  status: 'VALID' | 'INSUFFICIENT_SAMPLE' | 'EMPTY';
}

export interface HorizonMetrics {
  horizon: number;
  forward_return_stats: DistributionStats;
  mfe_stats: DistributionStats;
  mae_stats: DistributionStats;
  positive_count: number;
  negative_count: number;
  flat_count: number;
  insufficient_horizon_count: number;
  positive_ratio: number;
}

export interface ConditionalBreakdown {
  category: string;
  key: string;
  sample_count: number;
  horizon_metrics: Record<number, HorizonMetrics>;
}

export interface BacktestMetrics {
  total_candles: number;
  total_signals: number;
  long_signals: number;
  short_signals: number;
  wait_signals: number;
  neutral_signals: number;
  signals_per_day: number;
  signals_per_week: number;
  signals_per_month: number;
  horizon_metrics: Record<number, HorizonMetrics>;
  long_horizon_metrics: Record<number, HorizonMetrics>;
  short_horizon_metrics: Record<number, HorizonMetrics>;
  regime_breakdown: Record<string, ConditionalBreakdown>;
  strength_breakdown: Record<string, ConditionalBreakdown>;
  score_breakdown: Record<string, ConditionalBreakdown>;
  volatility_breakdown: Record<string, ConditionalBreakdown>;
  structure_breakdown: Record<string, ConditionalBreakdown>;
}

export interface IntegrityReport {
  future_leakage_detected: boolean;
  causal_processing: boolean;
  historical_data_modified: boolean;
  signal_immutability_verified: boolean;
  swing_confirmation_delay_verified: boolean;
  indicator_causality_verified: boolean;
  regime_causality_verified: boolean;
  structure_causality_verified: boolean;
  signal_causality_verified: boolean;
  checks_passed: boolean;
  details: string[];
}

export interface DatasetMetadata {
  dataset_id: string;
  symbol: string;
  timeframe: string;
  start_timestamp: number;
  end_timestamp: number;
  candle_count: number;
  gap_count: number;
  duplicate_count: number;
  sha256_hash: string;
  quality_status: string;
  download_timestamp: number;
  source: string;
}

export interface BacktestConfig {
  symbol: string;
  timeframe: string;
  warmup_bars: number;
  horizons: number[];
  cost_model: {
    enabled: boolean;
    fee_bps: number;
    slippage_bps: number;
  };
  backtest_engine_version: string;
  backtest_config_version: string;
}

export interface BacktestRun {
  run_id: string;
  symbol: string;
  timeframe: string;
  start_timestamp: number;
  end_timestamp: number;
  dataset_metadata: DatasetMetadata;
  config: BacktestConfig;
  metrics: BacktestMetrics;
  signal_outcomes: SignalOutcome[];
  integrity_report: IntegrityReport;
  status: string;
  created_timestamp: number;
  disclaimer: string;
}

export interface BacktestRunSummaryItem {
  run_id: string;
  symbol: string;
  timeframe: string;
  start_timestamp: number;
  end_timestamp: number;
  candle_count: number;
  signal_count: number;
  dataset_hash: string;
  status: string;
  created_timestamp: number;
  metrics_summary: {
    signals_per_day: number;
    long_signals: number;
    short_signals: number;
  };
}
