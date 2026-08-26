"""
Phase 9 — Real-Time Shadow / Paper Validation Domain Models.
Defines immutable schemas for live shadow signals, forward outcome tracking, sessions, and audits.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HorizonStatusEnum(str, Enum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    INSUFFICIENT_HORIZON = "INSUFFICIENT_HORIZON"


class SessionStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ABORTED = "ABORTED"


class FinalResearchStatusEnum(str, Enum):
    INSUFFICIENT_LIVE_DATA = "INSUFFICIENT_LIVE_DATA"
    CONTINUING_VALIDATION = "CONTINUING_VALIDATION"
    RESEARCH_OBSERVATION_COMPLETE = "RESEARCH_OBSERVATION_COMPLETE"


class DriftStatusEnum(str, Enum):
    ALIGNED = "ALIGNED"
    MILD_DRIFT = "MILD_DRIFT"
    SIGNIFICANT_DRIFT = "SIGNIFICANT_DRIFT"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"


class HorizonOutcome(BaseModel):
    """Immutable outcome observation for a single horizon (1, 3, 5, 10, 20 candles)."""
    horizon: int
    status: HorizonStatusEnum = HorizonStatusEnum.PENDING
    target_candle_close_time: Optional[int] = None
    target_close_price: Optional[float] = None
    raw_analytical_return: Optional[float] = None
    cost_adjusted_return_5bps: Optional[float] = None
    cost_adjusted_return_10bps: Optional[float] = None
    mfe: Optional[float] = None
    mae: Optional[float] = None
    completed_at_timestamp: Optional[int] = None


class ShadowSignal(BaseModel):
    """
    Immutable snapshot of a candidate signal generated at a verified closed candle.
    Signal parameters are strictly frozen at generation time.
    """
    signal_id: str
    session_id: str
    candidate_id: str  # "BASELINE", "EXP_A2_PULLBACK_VWAP", "EXP_E2_EXTENSION_VWAP"
    symbol: str
    timeframe: str
    candle_index: int
    candle_open_time: int
    candle_close_time: int
    entry_reference_price: float
    direction: str  # "LONG_SETUP", "SHORT_SETUP"
    signal_score: float
    signal_strength: str

    # Market context at signal time
    regime: str
    structure_state: str
    volatility_state: str

    # Evidence factor scores
    trend_score: float
    momentum_score: float
    structure_score: float
    volume_score: float
    volatility_score: float
    regime_score: float

    # Research anchor metrics
    vwap_price: Optional[float] = None
    vwap_distance_atr: Optional[float] = None
    ema21_price: Optional[float] = None
    ema21_distance_atr: Optional[float] = None
    atr: float = 1.0

    # Data provenance & causality
    data_quality_status: str = "HEALTHY"
    engine_version: str = "0.9.0-shadow"
    strategy_config_hash: str = ""
    causal_timestamp: int = 0
    received_at_timestamp: int = 0
    processing_latency_ms: float = 0.0

    # Forward outcomes (updated asynchronously as future candles close)
    outcomes: Dict[int, HorizonOutcome] = Field(default_factory=dict)


class CandidateLiveMetrics(BaseModel):
    """Aggregated live performance metrics for a single candidate stream."""
    candidate_id: str
    candidate_name: str
    total_signals: int = 0
    long_count: int = 0
    short_count: int = 0
    signals_per_day: float = 0.0
    pending_outcomes_count: int = 0
    completed_outcomes_count: int = 0
    incomplete_horizons_count: int = 0
    sample_status: str = "INSUFFICIENT_SAMPLE"

    # Forward return distributions
    h1_median_raw: float = 0.0
    h3_median_raw: float = 0.0
    h5_median_raw: float = 0.0
    h10_median_raw: float = 0.0
    h20_median_raw: float = 0.0

    h5_positive_rate: float = 0.0
    h10_positive_rate: float = 0.0
    h5_mfe_median: float = 0.0
    h5_mae_median: float = 0.0

    # Estimated cost-adjusted returns
    h5_median_cost_5bps: float = 0.0
    h5_median_cost_10bps: float = 0.0

    # Directional symmetry
    long_5c_median: float = 0.0
    short_5c_median: float = 0.0

    # Clustering
    adjacent_signal_rate: float = 0.0
    independent_episodes_count: int = 0


class DriftMetricComparison(BaseModel):
    """Observational comparison between live performance and Phase 8 historical benchmarks."""
    candidate_id: str
    metric_name: str
    historical_validation: float
    historical_test: float
    live_observed: float
    drift_delta: float
    drift_status: DriftStatusEnum
    details: str


class CausalAuditReport(BaseModel):
    """Automated causal integrity audit for a shadow validation session."""
    session_id: str
    audited_at_timestamp: int
    future_leakage_detected: bool = False
    future_outcome_used_during_signal_generation: bool = False
    candidate_configuration_changed: bool = False
    duplicate_signals_count: int = 0
    invalid_confirmed_candles_count: int = 0
    historical_signal_mutations_count: int = 0
    session_integrity_passed: bool = True
    integrity_notes: List[str] = Field(default_factory=list)


class ShadowSession(BaseModel):
    """State and metadata container for a persistent shadow validation session."""
    session_id: str
    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    start_time: int
    end_time: Optional[int] = None
    status: SessionStatusEnum = SessionStatusEnum.DRAFT
    final_research_status: FinalResearchStatusEnum = FinalResearchStatusEnum.INSUFFICIENT_LIVE_DATA

    # Provenance and immutable configuration hashes
    market_data_provider: str = "BinancePublicWebSocket"
    configuration_hashes: Dict[str, str] = Field(default_factory=dict)
    last_processed_candle_close_time: int = 0
    candles_processed_count: int = 0

    # Candidate metrics snapshots
    candidates_metrics: Dict[str, CandidateLiveMetrics] = Field(default_factory=dict)
    causal_audit: Optional[CausalAuditReport] = None
    is_read_only: bool = False
