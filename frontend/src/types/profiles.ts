export type ProfileId = 'SCALP_1M_V1' | 'INTRADAY_5M_V1' | 'TRADING_15M_V1' | 'SWING_4H_V1' | 'POSITION_1D_V1';

export type ProfileState = 'NO_TRADE' | 'WATCH' | 'SETUP' | 'ENTRY_READY' | 'INVALIDATED' | 'EXPIRED' | 'INSUFFICIENT_DATA';

export interface TradingProfileConfig {
  profile_id: string;
  display_name: string;
  description: string;
  profile_type: string;
  primary_timeframe: string;
  context_timeframes: string[];
  expected_holding_horizon: string;
  minimum_data_requirements: number;
  cost_sensitivity_bps: number[];
  status: string;
  config_hash: string;
}

export interface CostSensitivityTier {
  cost_bps: number;
  raw_analytical_return_pct: number;
  estimated_cost_adjusted_return_pct: number;
  cost_impact_pct: number;
  is_cost_viable: boolean;
  warning_flag?: string | null;
}

export interface ProfileAnalysisResult {
  profile_id: string;
  symbol: string;
  primary_timeframe: string;
  context_timeframes: string[];
  profile_state: ProfileState;
  state_description: string;
  trade_plan: any | null;
  context_confirmed: Record<string, boolean>;
  alignment_score: number;
  score_tier: string;
  cost_sensitivity: CostSensitivityTier[];
  cost_warning?: string | null;
  analytical_timestamp: number;
  is_preview: boolean;
  reasons: string[];
}

export interface ProfileComparisonItem {
  profile_id: string;
  display_name: string;
  primary_timeframe: string;
  context_timeframes: string[];
  expected_horizon: string;
  signals_per_day: number;
  clustering_factor: number;
  median_5c_return_pct: number;
  positive_rate_pct: number;
  avg_mfe_pct: number;
  avg_mae_pct: number;
  cost_viable_10bps: boolean;
  status: string;
}

export interface ProfileComparisonReport {
  generated_timestamp: number;
  symbol: string;
  profiles: ProfileComparisonItem[];
}
