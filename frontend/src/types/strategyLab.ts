export type ResearchStatus =
  | 'DRAFT'
  | 'RUNNING'
  | 'VALIDATION_FAILED'
  | 'VALIDATION_PASSED'
  | 'TEST_EVALUATED'
  | 'RESEARCH_PROMOTED'
  | 'CANDIDATE_FOR_PAPER_TRADING'
  | 'REJECTED';

export interface PartitionTimingMetrics {
  pre_1_median: number;
  pre_3_median: number;
  pre_5_median: number;
  pre_10_median: number;
  pre_20_median: number;
  post_1_median: number;
  post_3_median: number;
  post_5_median: number;
  post_10_median: number;
  post_20_median: number;
  pre_vs_post_5c_corr: number;
  trend_chasing_flag: boolean;
  timing_diagnostic: string;
}

export interface PartitionClusteringMetrics {
  adjacent_signal_rate: number;
  signals_within_2_bars: number;
  signals_within_4_bars: number;
  signals_within_8_bars: number;
  independent_episodes_count: number;
  avg_episode_length_bars: number;
  max_episode_length_bars: number;
}

export interface PartitionPerformanceMetrics {
  partition_name: string;
  start_timestamp: number;
  end_timestamp: number;
  candle_count: number;
  signal_count: number;
  long_count: number;
  short_count: number;
  signals_per_day: number;
  signals_per_100_candles: number;
  h1_median: number;
  h1_mean: number;
  h3_median: number;
  h3_mean: number;
  h5_median: number;
  h5_mean: number;
  h10_median: number;
  h10_mean: number;
  h20_median: number;
  h20_mean: number;
  long_5c_median: number;
  short_5c_median: number;
  long_10c_median: number;
  short_10c_median: number;
  long_20c_median: number;
  short_20c_median: number;
  positive_rate_5c: number;
  positive_rate_10c: number;
  mfe_5c_median: number;
  mae_5c_median: number;
  h5_median_cost_0bps: number;
  h5_median_cost_5bps: number;
  h5_median_cost_10bps: number;
  timing: PartitionTimingMetrics;
  clustering: PartitionClusteringMetrics;
  score_monotonicity_grade: string;
  score_spearman_corr: number;
  regime_breakdown: Record<string, { count: number; h5_median: number; pos_rate: number }>;
  sample_warning: string;
}

export interface PromotionGateResult {
  gate_id: string;
  gate_name: string;
  required_criterion: string;
  measured_value: string;
  passed: boolean;
  details: string;
}

export interface ExperimentEvaluation {
  experiment_id: string;
  experiment_name: string;
  description: string;
  hypothesis: string;
  parameters: Record<string, any>;
  engine_version: string;
  dataset_hash: string;
  created_timestamp: number;
  status: ResearchStatus;
  train_metrics: PartitionPerformanceMetrics;
  validation_metrics: PartitionPerformanceMetrics;
  test_metrics?: PartitionPerformanceMetrics;
  quarterly_metrics: PartitionPerformanceMetrics[];
  promotion_gates: PromotionGateResult[];
  gates_passed_count: number;
  total_gates_count: number;
  final_decision: string;
  decision_rationale: string;
}

export interface BaselineComparisonItem {
  metric_name: string;
  baseline_val: string;
  candidate_val: string;
  delta_str: string;
  improved: boolean;
  description: string;
}

export interface ExperimentComparisonReport {
  experiment_id: string;
  experiment_name: string;
  baseline_id: string;
  status: ResearchStatus;
  partition_evaluated: string;
  comparisons: BaselineComparisonItem[];
  promotion_status: string;
  summary_observed_facts: string[];
  summary_possible_explanations: string[];
  summary_unproven_hypotheses: string[];
}
