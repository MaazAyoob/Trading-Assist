"""
Configuration models for the Phase 6 Backtesting & Validation Engine.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from app.backtesting.version import BACKTEST_CONFIG_VERSION, BACKTEST_ENGINE_VERSION


class CostModelConfig(BaseModel):
    """
    Analytical execution-cost scenario configuration.
    Cost is applied symmetrically on entry and exit (round-trip).
    """
    enabled: bool = Field(default=False, description="Whether cost adjustments are applied")
    fee_bps: float = Field(default=10.0, ge=0.0, description="Exchange fee in basis points (e.g. 10 bps = 0.10%)")
    slippage_bps: float = Field(default=5.0, ge=0.0, description="Estimated slippage per side in bps (e.g. 5 bps = 0.05%)")
    is_round_trip: bool = Field(default=True, description="Whether fee and slippage apply to both entry and exit")

    @property
    def total_round_trip_fraction(self) -> float:
        """Returns the total round-trip cost as a decimal fraction (e.g. 0.0030 for 30 bps)."""
        if not self.enabled:
            return 0.0
        multiplier = 2.0 if self.is_round_trip else 1.0
        return (self.fee_bps + self.slippage_bps) * multiplier / 10000.0


class SplitConfig(BaseModel):
    """
    Chronological train / validation / test dataset partitioning.
    Zero shuffling — boundaries strictly preserve chronological order.
    """
    train_ratio: float = Field(default=0.60, ge=0.1, le=0.9, description="Chronological train split ratio")
    validation_ratio: float = Field(default=0.20, ge=0.0, le=0.5, description="Chronological validation split ratio")
    test_ratio: float = Field(default=0.20, ge=0.0, le=0.5, description="Chronological test holdout ratio")


class BacktestConfig(BaseModel):
    """
    Complete configuration for a backtest validation run.
    """
    symbol: str = Field(default="BTCUSDT")
    timeframe: str = Field(default="15m")
    start_timestamp: Optional[int] = Field(default=None, description="Optional filter start timestamp (ms)")
    end_timestamp: Optional[int] = Field(default=None, description="Optional filter end timestamp (ms)")
    warmup_bars: int = Field(default=50, ge=30, description="Minimum historical bars required before evaluating signals")
    horizons: List[int] = Field(default=[1, 3, 5, 10, 20], description="Evaluation forward horizons in candle counts")
    split: SplitConfig = Field(default_factory=SplitConfig)
    cost_model: CostModelConfig = Field(default_factory=CostModelConfig)
    bootstrap_seed: int = Field(default=42, description="Deterministic random seed for bootstrap resampling")
    bootstrap_iterations: int = Field(default=1000, ge=100, le=10000, description="Number of bootstrap resamples")
    block_bootstrap_length: int = Field(default=5, ge=1, le=100, description="Block length in signals for block bootstrap resampling")
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.999, description="Statistical confidence level")
    min_sample_size: int = Field(default=10, ge=3, description="Minimum sample size required before computing distributions")
    engine_mode: str = Field(default="CAUSAL_INCREMENTAL", description="Execution mode: CAUSAL_INCREMENTAL or CAUSAL_REFERENCE")
    
    # Explicit score bucket definitions
    score_buckets_positive: List[Tuple[float, float]] = Field(
        default=[(30.0, 40.0), (40.0, 50.0), (50.0, 60.0), (60.0, 70.0), (70.0, 80.0), (80.0, 100.0)]
    )
    score_buckets_negative: List[Tuple[float, float]] = Field(
        default=[(-100.0, -80.0), (-80.0, -70.0), (-70.0, -60.0), (-60.0, -50.0), (-50.0, -40.0), (-40.0, -30.0)]
    )
    
    backtest_engine_version: str = Field(default=BACKTEST_ENGINE_VERSION)
    backtest_config_version: str = Field(default=BACKTEST_CONFIG_VERSION)
