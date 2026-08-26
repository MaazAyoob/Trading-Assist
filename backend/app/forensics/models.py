"""
Phase 7 — Signal Forensics & Factor Attribution Domain Models.
Strictly analytical, non-mutating forensic data schemas.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ScoreTraceRecord(BaseModel):
    """Auditable mathematical trace of a single historical signal."""
    signal_id: str
    candle_index: int
    timestamp: int
    close_price: float
    direction: str
    strength: str
    status: str

    # Factor scores (group scores on [-100.0, +100.0])
    trend_score: float
    momentum_score: float
    structure_score: float
    volume_score: float
    volatility_score: float
    regime_score: float

    # Factor weighted contributions to raw score
    trend_contribution: float
    momentum_contribution: float
    structure_contribution: float
    volume_contribution: float

    # Score components
    raw_score: float
    regime_modifier: float
    volatility_modifier: float
    conflict_penalty: float
    net_score: float

    # Pre-signal returns (% change over preceding H bars)
    pre_returns: Dict[int, float] = Field(default_factory=dict)
    # Post-signal returns (% forward analytical return over H bars)
    post_returns: Dict[int, float] = Field(default_factory=dict)

    # Context at signal time
    regime_at_signal: str = "UNKNOWN"
    structure_at_signal: str = "UNKNOWN"
    volatility_at_signal: str = "NORMAL"
    nearest_res_distance_atr: Optional[float] = None
    nearest_sup_distance_atr: Optional[float] = None
    recent_structural_event: str = "NONE"
    conflicts_present: List[str] = Field(default_factory=list)


class FactorPerformanceBin(BaseModel):
    """Forward outcome statistics conditioned on a factor score bin."""
    factor_name: str
    bin_label: str
    min_score: float
    max_score: float
    sample_count: int
    sample_warning: str = "VALID"
    # horizon -> {mean, median, pos_pct, mfe_median, mae_median, n}
    outcomes: Dict[int, Dict[str, float]] = Field(default_factory=dict)


class FactorMonotonicityEvaluation(BaseModel):
    """Deterministic mathematical assessment of factor-to-return monotonicity."""
    factor_name: str
    horizon: int
    direction: str  # "LONG", "SHORT", "ALL"
    monotonicity_grade: str  # "MONOTONIC", "WEAKLY_MONOTONIC", "NON_MONOTONIC", "INVERSE"
    criteria_description: str
    spearman_correlation: float
    bin_medians: Dict[str, float]


class SignalTimingForensics(BaseModel):
    """Pre-signal vs Post-signal return timing and trend-chasing diagnostic."""
    direction: str  # "LONG", "SHORT", "COMBINED"
    horizons: List[int]
    pre_signal_mean_returns: Dict[int, float]
    pre_signal_median_returns: Dict[int, float]
    post_signal_mean_returns: Dict[int, float]
    post_signal_median_returns: Dict[int, float]
    pre_vs_post_correlation: Dict[int, float]
    trend_chasing_flag: bool
    trend_chasing_diagnostic: str
    reversal_vs_continuation_classification: str  # "CONTINUATION", "REVERSAL", "MIXED", "UNCLEAR"
    classification_criteria: str


class SignalClusteringForensics(BaseModel):
    """Signal arrival interval, clustering frequency, and directional persistence metrics."""
    total_signals: int
    mean_interval_candles: float
    median_interval_candles: float
    min_interval_candles: int
    pct_within_1_candle: float
    pct_within_2_candles: float
    pct_within_4_candles: float
    pct_within_8_candles: float
    effective_sample_size_estimate: int
    dependence_warning: str
    # Directional persistence runs
    long_runs_count: int
    short_runs_count: int
    long_run_lengths_avg: float
    short_run_lengths_avg: float
    max_long_run_length: int
    max_short_run_length: int
    run_length_distribution: Dict[str, int]


class RegimeForensicsRecord(BaseModel):
    """Forensic performance breakdown by market regime at signal time."""
    regime_name: str
    signal_count: int
    long_count: int
    short_count: int
    sample_warning: str = "VALID"
    h1_median_return: float
    h3_median_return: float
    h5_median_return: float
    h10_median_return: float
    h20_median_return: float
    h5_positive_rate: float
    h10_positive_rate: float
    avg_trend_score: float
    avg_momentum_score: float
    avg_structure_score: float
    avg_volume_score: float


class StructureForensicsRecord(BaseModel):
    """Forensic breakdown by structural event confirmed at signal time."""
    event_category: str  # "BULLISH_BOS", "BEARISH_BOS", "BULLISH_CHOCH", "BEARISH_CHOCH", "NO_RECENT_EVENT"
    signal_count: int
    long_count: int
    short_count: int
    sample_warning: str = "VALID"
    h1_median_return: float
    h3_median_return: float
    h5_median_return: float
    h10_median_return: float
    h20_median_return: float
    h5_positive_rate: float


class SRDistanceForensicsRecord(BaseModel):
    """Forensic breakdown by distance to nearest Support / Resistance zone in ATR."""
    distance_bucket: str  # "<0.25 ATR", "0.25-0.5 ATR", "0.5-1 ATR", "1-2 ATR", ">2 ATR"
    target_zone_type: str  # "RESISTANCE" for Long, "SUPPORT" for Short
    signal_count: int
    sample_warning: str = "VALID"
    h1_median_return: float
    h3_median_return: float
    h5_median_return: float
    h10_median_return: float
    h20_median_return: float
    h5_positive_rate: float


class ConflictForensicsRecord(BaseModel):
    """Forensic effectiveness analysis of individual conflict penalty rules."""
    conflict_id: str
    category: str
    signal_count: int
    mean_penalty: float
    h1_median_return: float
    h5_median_return: float
    h10_median_return: float
    h5_positive_rate: float
    effectiveness_assessment: str


class ScoreCalibrationRecord(BaseModel):
    """Score bucket vs subsequent return calibration record."""
    score_bucket: str
    direction: str
    signal_count: int
    sample_warning: str = "VALID"
    h1_median_return: float
    h3_median_return: float
    h5_median_return: float
    h10_median_return: float
    h20_median_return: float
    h5_positive_rate: float
    h10_positive_rate: float


class PartitionForensicsRecord(BaseModel):
    """Forensics for Train/Validation/Test splits and quarterly periods."""
    partition_name: str
    start_timestamp: int
    end_timestamp: int
    start_date: str
    end_date: str
    candle_count: int
    signal_count: int
    long_count: int
    short_count: int
    signals_per_day: float
    h1_median_return: float
    h5_median_return: float
    h10_median_return: float
    h20_median_return: float
    h5_positive_rate: float


class ForensicsReport(BaseModel):
    """Complete, self-contained Phase 7 Forensic Research Report."""
    run_id: str
    symbol: str
    timeframe: str
    dataset_id: str
    dataset_sha256: str
    start_timestamp: int
    end_timestamp: int
    candle_count: int
    total_signals: int
    long_signals: int
    short_signals: int
    runtime_seconds: float
    created_timestamp: int

    # Core Forensic Sections
    score_traces_sample: List[ScoreTraceRecord]
    factor_performance: List[FactorPerformanceBin]
    factor_monotonicity: List[FactorMonotonicityEvaluation]
    timing_long: SignalTimingForensics
    timing_short: SignalTimingForensics
    timing_combined: SignalTimingForensics
    clustering: SignalClusteringForensics
    regime_forensics: List[RegimeForensicsRecord]
    structure_forensics: List[StructureForensicsRecord]
    sr_distance_forensics: List[SRDistanceForensicsRecord]
    conflict_forensics: List[ConflictForensicsRecord]
    score_calibration: List[ScoreCalibrationRecord]
    score_monotonicity_grade: str
    score_monotonicity_criteria: str
    partitions: List[PartitionForensicsRecord]
    quarterly: List[PartitionForensicsRecord]

    # Explicit 3-Section Final Research Diagnosis
    observed_facts: List[str]
    possible_explanations: List[str]
    unproven_hypotheses: List[str]
