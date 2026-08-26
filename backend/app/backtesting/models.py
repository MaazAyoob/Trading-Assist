"""
Domain and data models for Phase 6 Backtesting & Validation Engine.
Strictly non-predictive, analytical outcome structures.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.backtesting.config import BacktestConfig


class OutcomeClassificationEnum(str, Enum):
    POSITIVE_FORWARD_RETURN = "POSITIVE_FORWARD_RETURN"
    NEGATIVE_FORWARD_RETURN = "NEGATIVE_FORWARD_RETURN"
    FLAT_FORWARD_RETURN = "FLAT_FORWARD_RETURN"
    INSUFFICIENT_HORIZON = "INSUFFICIENT_HORIZON"


class HorizonOutcome(BaseModel):
    """
    Evaluation outcome for a single signal at a specific future candle horizon (e.g. 5 candles).
    """
    horizon: int = Field(description="Horizon distance in candle count")
    future_close: Optional[float] = Field(default=None, description="Close price at horizon index (i + h)")
    forward_return: Optional[float] = Field(default=None, description="Analytical directional return as decimal (e.g. 0.02 = +2.0%)")
    mfe: Optional[float] = Field(default=None, description="Maximum Favorable Excursion as positive decimal")
    mae: Optional[float] = Field(default=None, description="Maximum Adverse Excursion as negative decimal")
    status: OutcomeClassificationEnum = Field(default=OutcomeClassificationEnum.INSUFFICIENT_HORIZON)
    estimated_net_forward_return: Optional[float] = Field(default=None, description="Forward return adjusted for analytical cost scenario")


class SignalOutcome(BaseModel):
    """
    Complete historical evaluation record for a single confirmed research signal.
    """
    signal_id: str
    symbol: str
    timeframe: str
    signal_timestamp: int = Field(description="Candle close timestamp when signal became confirmed (ms)")
    signal_direction: str = Field(description="LONG_SETUP or SHORT_SETUP")
    signal_strength: str = Field(description="VERY_WEAK, WEAK, MODERATE, STRONG, VERY_STRONG")
    signal_score: float = Field(description="Net directional score (-100 to +100)")
    entry_reference_price: float = Field(description="Close price of the signal candle (C_i)")
    outcomes: Dict[int, HorizonOutcome] = Field(default_factory=dict, description="Horizon outcomes mapped by horizon int (e.g. 1, 3, 5, 10, 20)")
    regime_at_signal: str = Field(description="Market regime classification snapshot at signal time")
    structure_at_signal: str = Field(description="Market structure direction snapshot at signal time")
    volatility_at_signal: str = Field(description="Volatility state snapshot at signal time")
    engine_version: str
    config_version: str


class GapRecord(BaseModel):
    """Provenance record of an individual interval gap in the historical candle sequence."""
    gap_start: int = Field(description="Start timestamp of the gap in ms (UTC)")
    gap_end: int = Field(description="End timestamp of the gap in ms (UTC)")
    missing_candle_count: int = Field(description="Estimated number of missing candles")


class DistributionStats(BaseModel):
    """
    Parametric and non-parametric statistical metrics for an outcome distribution.
    """
    sample_count: int = 0
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    std_error: Optional[float] = None
    ci_lower_normal: Optional[float] = None
    ci_upper_normal: Optional[float] = None
    bootstrap_mean_ci_lower: Optional[float] = None
    bootstrap_mean_ci_upper: Optional[float] = None
    bootstrap_median_ci_lower: Optional[float] = None
    bootstrap_median_ci_upper: Optional[float] = None
    block_bootstrap_mean_ci_lower: Optional[float] = None
    block_bootstrap_mean_ci_upper: Optional[float] = None
    p5: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p95: Optional[float] = None
    status: str = Field(default="VALID", description="VALID, INSUFFICIENT_SAMPLE, or EMPTY")
    sample_warning: Optional[str] = Field(default=None, description="VALID, SMALL_SAMPLE (<30), or INSUFFICIENT_SAMPLE (<10)")


class HorizonMetrics(BaseModel):
    """
    Aggregated statistical summary across all signals for a specific horizon.
    """
    horizon: int
    forward_return_stats: DistributionStats = Field(default_factory=DistributionStats)
    mfe_stats: DistributionStats = Field(default_factory=DistributionStats)
    mae_stats: DistributionStats = Field(default_factory=DistributionStats)
    positive_count: int = 0
    negative_count: int = 0
    flat_count: int = 0
    insufficient_horizon_count: int = 0
    positive_ratio: float = 0.0


class ConditionalBreakdown(BaseModel):
    """
    Performance slice conditioned on an internal state (e.g. Regime == TRENDING_BULLISH).
    """
    category: str = Field(description="Condition category: REGIME, STRENGTH, SCORE_RANGE, VOLATILITY, STRUCTURE, SUBPERIOD")
    key: str = Field(description="Specific slice key: e.g. TRENDING_BULLISH, STRONG, 50-60, 2024-Q1")
    sample_count: int = 0
    horizon_metrics: Dict[int, HorizonMetrics] = Field(default_factory=dict)


class BacktestMetrics(BaseModel):
    """
    Comprehensive multi-dimensional metrics produced by the backtester.
    """
    total_candles: int = 0
    total_signals: int = 0
    long_signals: int = 0
    short_signals: int = 0
    wait_signals: int = 0
    neutral_signals: int = 0
    signals_per_day: float = 0.0
    signals_per_week: float = 0.0
    signals_per_month: float = 0.0
    
    # Combined Directional Metrics
    horizon_metrics: Dict[int, HorizonMetrics] = Field(default_factory=dict)
    
    # Directional Symmetry Breakdowns
    long_horizon_metrics: Dict[int, HorizonMetrics] = Field(default_factory=dict)
    short_horizon_metrics: Dict[int, HorizonMetrics] = Field(default_factory=dict)
    
    # Conditional Breakdowns
    regime_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)
    strength_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)
    score_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)
    volatility_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)
    structure_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)
    subperiod_breakdown: Dict[str, ConditionalBreakdown] = Field(default_factory=dict)


class IntegrityReport(BaseModel):
    """
    Mandatory audit verification ensuring zero future data leakage,
    strict causal sequential simulation, and signal immutability.
    """
    future_leakage_detected: bool = False
    causal_processing: bool = True
    historical_data_modified: bool = False
    signal_immutability_verified: bool = True
    swing_confirmation_delay_verified: bool = True
    indicator_causality_verified: bool = True
    regime_causality_verified: bool = True
    structure_causality_verified: bool = True
    signal_causality_verified: bool = True
    checks_passed: bool = True
    details: List[str] = Field(default_factory=list)


class DatasetMetadata(BaseModel):
    """
    Provenance and reproducibility record for a historical candle dataset.
    """
    dataset_id: str
    symbol: str
    timeframe: str
    start_timestamp: int
    end_timestamp: int
    candle_count: int
    gap_count: int = 0
    duplicate_count: int = 0
    invalid_count: int = 0
    dataset_version: str = "v1.0"
    gaps: List[GapRecord] = Field(default_factory=list)
    sha256_hash: str
    quality_status: str
    download_timestamp: int
    source: str = "BINANCE_PUBLIC_REST"


class BacktestRun(BaseModel):
    """
    Root entity representing a reproducible historical backtesting run.
    """
    run_id: str
    symbol: str
    timeframe: str
    start_timestamp: int
    end_timestamp: int
    dataset_metadata: DatasetMetadata
    config: BacktestConfig
    metrics: BacktestMetrics
    signal_outcomes: List[SignalOutcome] = Field(default_factory=list)
    integrity_report: IntegrityReport
    status: str = "COMPLETED"
    created_timestamp: int
    runtime_seconds: Optional[float] = None
    candles_per_second: Optional[float] = None
    signals_per_second: Optional[float] = None
    disclaimer: str = (
        "Phase 6 measures historical analytical forward returns and excursion profiles. "
        "It does not establish future profitability, trade execution feasibility, or guaranteed returns."
    )
