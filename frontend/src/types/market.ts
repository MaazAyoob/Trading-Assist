export type Timeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

export type CandleState = 'OPEN' | 'UPDATING' | 'CLOSED';
export type ConnectionState = 'LIVE' | 'RECONNECTING' | 'OFFLINE';
export type QualityStatus = 'HEALTHY' | 'WARNING' | 'INVALID' | 'INSUFFICIENT_DATA';

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_time?: number;
  quote_volume?: number;
  trades_count?: number;
  is_closed?: boolean;
  state?: CandleState;
}

export interface Ticker {
  symbol: string;
  price: number;
  price_change: number;
  price_change_percent: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  quote_volume_24h: number;
  timestamp: number;
}

export interface MarketConnectionStatus {
  state: ConnectionState;
  symbol: string;
  timeframe: string;
  last_ping: number;
  last_message_time: number;
  reconnect_attempts: number;
  message: string;
}

export interface MarketDataQuality {
  symbol: string;
  timeframe: string;
  status: QualityStatus;
  total_candles: number;
  valid_candles: number;
  gap_count: number;
  duplicate_count: number;
  out_of_order_count: number;
  is_stale: boolean;
  details: string[];
}

export interface TrendIndicators {
  ema_9?: number;
  ema_21?: number;
  ema_50?: number;
  ema_100?: number;
  ema_200?: number;
  vwap?: number;
  adx?: number;
  plus_di?: number;
  minus_di?: number;
  supertrend?: number;
  supertrend_direction?: number;
}

export interface MomentumIndicators {
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  stoch_rsi_k?: number;
  stoch_rsi_d?: number;
  roc?: number;
}

export interface VolatilityIndicators {
  atr?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  bb_bandwidth?: number;
  bb_percent_b?: number;
}

export interface VolumeIndicators {
  volume_sma?: number;
  relative_volume?: number;
  obv?: number;
}

export interface IndicatorSnapshot {
  symbol: string;
  timeframe: string;
  timestamp: number;
  candle_state: CandleState;
  is_confirmed: boolean;
  trend: TrendIndicators;
  momentum: MomentumIndicators;
  volatility: VolatilityIndicators;
  volume: VolumeIndicators;
  quality_status: QualityStatus;
  engine_version: string;
  config_version: string;
}

export interface IndicatorHistoryPoint {
  timestamp: number;
  ema_9?: number;
  ema_21?: number;
  ema_50?: number;
  ema_200?: number;
  vwap?: number;
  supertrend?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  atr?: number;
  relative_volume?: number;
  obv?: number;
}

export interface EvidenceItem {
  category: string;
  description: string;
  metric_value?: string;
  is_supporting: boolean;
}

export interface MarketRegimeSnapshot {
  symbol: string;
  timeframe: string;
  timestamp: number;
  candle_state: CandleState;
  is_confirmed: boolean;
  direction: 'BULLISH' | 'BEARISH' | 'RANGE' | 'UNCERTAIN';
  trend_strength: 'NONE' | 'WEAK' | 'MODERATE' | 'STRONG' | 'VERY_STRONG';
  volatility_state: 'VERY_LOW' | 'LOW' | 'NORMAL' | 'HIGH' | 'EXTREME';
  momentum_state: 'VERY_POSITIVE' | 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE' | 'VERY_NEGATIVE';
  volume_state: 'LOW' | 'NORMAL' | 'ABOVE_AVERAGE' | 'HIGH_EXPANSION';
  structure_state: 'BULLISH' | 'BEARISH' | 'RANGE' | 'TRANSITION' | 'UNKNOWN';
  overall_regime: 'TRENDING_BULLISH' | 'TRENDING_BEARISH' | 'RANGING' | 'HIGH_VOLATILITY' | 'LOW_VOLATILITY' | 'TRANSITION' | 'UNCERTAIN';
  evidence_strength: number;
  evidence: EvidenceItem[];
  contradictions: EvidenceItem[];
  regime_engine_version: string;
  regime_config_version: string;
}

export interface SwingPoint {
  swing_id: string;
  swing_type: 'SWING_HIGH' | 'SWING_LOW';
  price: number;
  candle_timestamp: number;
  confirmation_timestamp?: number;
  is_confirmed: boolean;
}

export interface StructureEvent {
  event_id: string;
  event_type: 'BULLISH_BOS' | 'BEARISH_BOS' | 'BULLISH_CHOCH' | 'BEARISH_CHOCH';
  broken_swing_id: string;
  broken_level: number;
  break_timestamp: number;
  confirmation_timestamp: number;
  close_price: number;
  break_distance: number;
  atr_normalized_distance: number;
  volume_ratio: number;
  candle_body_ratio: number;
  break_quality: 'STRONG_BREAK' | 'NORMAL_BREAK' | 'WEAK_BREAK';
  is_confirmed: boolean;
}

export interface SupportResistanceZone {
  zone_id: string;
  zone_type: 'SUPPORT' | 'RESISTANCE';
  price_low: number;
  price_high: number;
  price_center: number;
  touch_count: number;
  strength: 'WEAK' | 'MODERATE' | 'STRONG';
  status: 'ACTIVE' | 'TESTED' | 'BROKEN' | 'INVALIDATED';
  created_timestamp: number;
  last_touch_timestamp: number;
}

export interface MarketStructureSnapshot {
  symbol: string;
  timeframe: string;
  timestamp: number;
  candle_state: CandleState;
  is_confirmed: boolean;
  structure_direction: 'BULLISH' | 'BEARISH' | 'RANGE' | 'TRANSITION' | 'UNKNOWN';
  confirmed_swings: SwingPoint[];
  developing_swings: SwingPoint[];
  active_structural_high?: SwingPoint;
  active_structural_low?: SwingPoint;
  bos_events: StructureEvent[];
  choch_events: StructureEvent[];
  support_zones: SupportResistanceZone[];
  resistance_zones: SupportResistanceZone[];
  structure_engine_version: string;
  structure_config_version: string;
}

// Phase 5 Multi-Factor Signal Research Types
export type SignalDirection = 'LONG_SETUP' | 'SHORT_SETUP' | 'NEUTRAL';
export type SignalStrength = 'VERY_WEAK' | 'WEAK' | 'MODERATE' | 'STRONG' | 'VERY_STRONG';
export type SignalStatus = 'VALID' | 'WAIT' | 'INSUFFICIENT_DATA' | 'CONFLICTED' | 'INVALID_DATA';
export type ConflictSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface EvidenceComponent {
  name: string;
  raw_value: string;
  contribution: number;
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  explanation: string;
}

export interface EvidenceGroupScore {
  group_name: string;
  score: number;
  weight: number;
  weighted_contribution: number;
  state: string;
  components: EvidenceComponent[];
}

export interface ConflictItem {
  conflict_id: string;
  category: string;
  severity: ConflictSeverity;
  raw_penalty: number;
  applied_penalty: number;
  explanation: string;
  affected_groups: string[];
}

export interface ScoreTrace {
  trend_score: number;
  momentum_score: number;
  structure_score: number;
  volume_score: number;
  base_directional_score: number;
  regime_modifier: number;
  volatility_modifier: number;
  context_adjusted_score: number;
  total_conflict_penalty: number;
  net_score: number;
}

export interface ResearchSignal {
  symbol: string;
  timeframe: string;
  timestamp: number;
  candle_state: CandleState;
  is_confirmed: boolean;
  is_historical: boolean;
  direction: SignalDirection;
  strength: SignalStrength;
  status: SignalStatus;
  score: number;
  evidence_groups: Record<string, EvidenceGroupScore>;
  score_trace: ScoreTrace;
  conflicts: ConflictItem[];
  supporting_evidence: string[];
  contradictions: string[];
  data_quality_status: string;
  disclaimer: string;
  engine_version: string;
  config_version: string;
}

export interface ChartOverlaySettings {
  ema9: boolean;
  ema21: boolean;
  ema50: boolean;
  ema200: boolean;
  vwap: boolean;
  bollinger: boolean;
  supertrend: boolean;
  swings: boolean;
  bos: boolean;
  zones: boolean;
  signalMarkers: boolean;
  tradePlan: boolean;
}

export interface WebSocketMessage {
  type: string;
  symbol: string;
  timeframe: string;
  candle?: Candle;
  candle_state?: CandleState;
  ticker?: Ticker;
  server_time?: number;
  status?: MarketConnectionStatus;
  indicators?: {
    confirmed?: IndicatorSnapshot;
    realtime?: IndicatorSnapshot;
  };
  regime?: {
    confirmed?: MarketRegimeSnapshot;
    realtime?: MarketRegimeSnapshot;
  };
  structure?: {
    confirmed?: MarketStructureSnapshot;
    realtime?: MarketStructureSnapshot;
  };
  signal?: {
    confirmed?: ResearchSignal;
    realtime?: ResearchSignal;
  };
  trade_decision?: {
    confirmed?: any;
    realtime?: any;
  };
}
