export interface FactorPerformanceBin {
  factor_name: string;
  bin_label: string;
  min_score: number;
  max_score: number;
  sample_count: number;
  sample_warning: string;
  outcomes: Record<number, {
    mean: number;
    median: number;
    positive_ratio: number;
    sample_count: number;
  }>;
}

export interface FactorMonotonicityEvaluation {
  factor_name: string;
  horizon: number;
  direction: string;
  monotonicity_grade: 'MONOTONIC' | 'WEAKLY_MONOTONIC' | 'NON_MONOTONIC' | 'INVERSE';
  criteria_description: string;
  spearman_correlation: number;
  bin_medians: Record<string, number>;
}

export interface SignalTimingForensics {
  direction: string;
  horizons: number[];
  pre_signal_mean_returns: Record<number, number>;
  pre_signal_median_returns: Record<number, number>;
  post_signal_mean_returns: Record<number, number>;
  post_signal_median_returns: Record<number, number>;
  pre_vs_post_correlation: Record<number, number>;
  trend_chasing_flag: boolean;
  trend_chasing_diagnostic: string;
  reversal_vs_continuation_classification: string;
  classification_criteria: string;
}

export interface SignalClusteringForensics {
  total_signals: number;
  mean_interval_candles: number;
  median_interval_candles: number;
  min_interval_candles: number;
  pct_within_1_candle: number;
  pct_within_2_candles: number;
  pct_within_4_candles: number;
  pct_within_8_candles: number;
  effective_sample_size_estimate: number;
  dependence_warning: string;
  long_runs_count: number;
  short_runs_count: number;
  long_run_lengths_avg: number;
  short_run_lengths_avg: number;
  max_long_run_length: number;
  max_short_run_length: number;
  run_length_distribution: Record<string, number>;
}

export interface RegimeForensicsRecord {
  regime_name: string;
  signal_count: number;
  long_count: number;
  short_count: number;
  sample_warning: string;
  h1_median_return: number;
  h3_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h20_median_return: number;
  h5_positive_rate: number;
  h10_positive_rate: number;
  avg_trend_score: number;
  avg_momentum_score: number;
  avg_structure_score: number;
  avg_volume_score: number;
}

export interface StructureForensicsRecord {
  event_category: string;
  signal_count: number;
  long_count: number;
  short_count: number;
  sample_warning: string;
  h1_median_return: number;
  h3_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h20_median_return: number;
  h5_positive_rate: number;
}

export interface SRDistanceForensicsRecord {
  distance_bucket: string;
  target_zone_type: string;
  signal_count: number;
  sample_warning: string;
  h1_median_return: number;
  h3_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h20_median_return: number;
  h5_positive_rate: number;
}

export interface ConflictForensicsRecord {
  conflict_id: string;
  category: string;
  signal_count: number;
  mean_penalty: number;
  h1_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h5_positive_rate: number;
  effectiveness_assessment: string;
}

export interface ScoreCalibrationRecord {
  score_bucket: string;
  direction: string;
  signal_count: number;
  sample_warning: string;
  h1_median_return: number;
  h3_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h20_median_return: number;
  h5_positive_rate: number;
  h10_positive_rate: number;
}

export interface PartitionForensicsRecord {
  partition_name: string;
  start_timestamp: number;
  end_timestamp: number;
  start_date: string;
  end_date: string;
  candle_count: number;
  signal_count: number;
  long_count: number;
  short_count: number;
  signals_per_day: number;
  h1_median_return: number;
  h5_median_return: number;
  h10_median_return: number;
  h20_median_return: number;
  h5_positive_rate: number;
}

export interface ForensicsReport {
  run_id: string;
  symbol: string;
  timeframe: string;
  dataset_id: string;
  dataset_sha256: string;
  start_timestamp: number;
  end_timestamp: number;
  candle_count: number;
  total_signals: number;
  long_signals: number;
  short_signals: number;
  runtime_seconds: number;
  created_timestamp: number;
  factor_performance: FactorPerformanceBin[];
  factor_monotonicity: FactorMonotonicityEvaluation[];
  timing_long: SignalTimingForensics;
  timing_short: SignalTimingForensics;
  timing_combined: SignalTimingForensics;
  clustering: SignalClusteringForensics;
  regime_forensics: RegimeForensicsRecord[];
  structure_forensics: StructureForensicsRecord[];
  sr_distance_forensics: SRDistanceForensicsRecord[];
  conflict_forensics: ConflictForensicsRecord[];
  score_calibration: ScoreCalibrationRecord[];
  score_monotonicity_grade: string;
  score_monotonicity_criteria: string;
  partitions: PartitionForensicsRecord[];
  quarterly: PartitionForensicsRecord[];
  observed_facts: string[];
  possible_explanations: string[];
  unproven_hypotheses: string[];
}
