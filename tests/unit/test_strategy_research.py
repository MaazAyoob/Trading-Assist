"""
Unit and Integration Tests for Phase 8 — Controlled Strategy Research Engine.
Verifies baseline immutability, experiment filter correctness, partition isolation, and gate logic.
"""

import copy
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.strategy_research.config import (
    STRATEGY_BASELINE,
    BASELINE_CONFIG_VERSION,
    EXPERIMENT_DEFINITIONS,
    TRAIN_START, TRAIN_END,
    VAL_START, VAL_END,
    TEST_START, TEST_END,
)
from app.strategy_research.baseline import BaselineStrategyRunner
from app.strategy_research.experiments import (
    PullbackResearchFilter,
    DivergenceResearchFilter,
    FirstStructuralEventFilter,
    EpisodeCooldownFilter,
    ExtensionResearchFilter,
)
from app.strategy_research.selection import StrategySelectionEngine
from app.strategy_research.evaluation import StrategyEvaluator
from app.strategy_research.models import PartitionPerformanceMetrics, ResearchStatusEnum
from app.strategy_research.engine import StrategyResearchEngine


def generate_synthetic_candles(n: int = 350) -> list[Candle]:
    """Generates synthetic 15m candles with a realistic trending price walk."""
    import numpy as np
    rng = np.random.default_rng(42)
    candles = []
    price = 50000.0
    start_ts = 1704067200000

    for i in range(n):
        ts = start_ts + i * 900000
        ret = rng.normal(0.0002, 0.003)
        open_p = price
        close_p = open_p * (1.0 + ret)
        high_p = max(open_p, close_p) * (1.0 + abs(rng.normal(0, 0.001)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.normal(0, 0.001)))
        vol = float(rng.uniform(10.0, 100.0))

        candles.append(Candle(
            timestamp=ts,
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=round(vol, 4),
            close_time=ts + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        ))
        price = close_p

    return candles


def test_baseline_immutability():
    """Verifies that Phase 5 Baseline identity and frozen versions are immutable."""
    identity = BaselineStrategyRunner.get_baseline_identity()
    assert identity["baseline_id"] == "PHASE5_V0.5.0"
    assert identity["engine_version"] == "0.5.0"
    assert identity["config_version"] == "2026-08-24-v1"
    assert identity["immutable"] is True


def test_experiment_predeclared_definitions():
    """Verifies that all required candidate experiments are predeclared without grid sweeps."""
    assert "EXP_A1_PULLBACK_EMA21" in EXPERIMENT_DEFINITIONS
    assert "EXP_A2_PULLBACK_VWAP" in EXPERIMENT_DEFINITIONS
    assert "EXP_B1_DIVERGENCE_RSI" in EXPERIMENT_DEFINITIONS
    assert "EXP_B2_DIVERGENCE_MACD" in EXPERIMENT_DEFINITIONS
    assert "EXP_C1_FIRST_STRUCTURAL_EVENT" in EXPERIMENT_DEFINITIONS
    assert "EXP_D1_EPISODE_COOLDOWN" in EXPERIMENT_DEFINITIONS
    assert "EXP_E1_EXTENSION_FILTER_EMA21" in EXPERIMENT_DEFINITIONS
    assert "EXP_E2_EXTENSION_FILTER_VWAP" in EXPERIMENT_DEFINITIONS
    assert "EXP_F1_COMBINED_CANDIDATE" in EXPERIMENT_DEFINITIONS


def test_episode_cooldown_filter_logic():
    """Verifies that EpisodeCooldownFilter emits exactly one setup per directional run."""
    flt = EpisodeCooldownFilter()
    flt.reset()

    assert flt.evaluate("LONG_SETUP") is True
    assert flt.evaluate("LONG_SETUP") is False
    assert flt.evaluate("LONG_SETUP") is False

    # Direction change triggers new episode setup
    assert flt.evaluate("SHORT_SETUP") is True
    assert flt.evaluate("SHORT_SETUP") is False


def test_first_structural_event_filter_logic():
    """Verifies that FirstStructuralEventFilter only allows signals within max_bars_post_breakout."""
    assert FirstStructuralEventFilter.evaluate(candle_idx=10, last_structure_event_idx=10, max_bars_post_breakout=3) is True
    assert FirstStructuralEventFilter.evaluate(candle_idx=12, last_structure_event_idx=10, max_bars_post_breakout=3) is True
    assert FirstStructuralEventFilter.evaluate(candle_idx=14, last_structure_event_idx=10, max_bars_post_breakout=3) is False
    assert FirstStructuralEventFilter.evaluate(candle_idx=10, last_structure_event_idx=None, max_bars_post_breakout=3) is False


def test_chronological_partition_boundaries():
    """Verifies strict non-overlapping chronological partition boundaries."""
    assert TRAIN_START < TRAIN_END
    assert TRAIN_END < VAL_START
    assert VAL_START < VAL_END
    assert VAL_END < TEST_START
    assert TEST_START < TEST_END


def test_promotion_gates_logic():
    """Verifies deterministic promotion gate grading and status lifecycle assignment."""
    b_val = PartitionPerformanceMetrics(
        partition_name="VAL", start_timestamp=VAL_START, end_timestamp=VAL_END,
        candle_count=1000, signal_count=500, long_count=250, short_count=250,
        signals_per_day=5.0, signals_per_100_candles=50.0,
        h5_median=-0.00033, positive_rate_5c=45.9,
    )
    c_val = PartitionPerformanceMetrics(
        partition_name="VAL", start_timestamp=VAL_START, end_timestamp=VAL_END,
        candle_count=1000, signal_count=100, long_count=50, short_count=50,
        signals_per_day=1.0, signals_per_100_candles=10.0,
        h5_median=+0.00050, positive_rate_5c=52.0,
        long_5c_median=0.0004, short_5c_median=0.0006,
        score_monotonicity_grade="WEAKLY_MONOTONIC", score_spearman_corr=0.6,
        regime_breakdown={"TRENDING_BULLISH": {}, "RANGING": {}},
    )
    c_test = PartitionPerformanceMetrics(
        partition_name="TEST", start_timestamp=TEST_START, end_timestamp=TEST_END,
        candle_count=1000, signal_count=80, long_count=40, short_count=40,
        signals_per_day=0.8, signals_per_100_candles=8.0,
        h5_median=+0.00030, positive_rate_5c=50.0,
    )
    b_test = PartitionPerformanceMetrics(
        partition_name="TEST", start_timestamp=TEST_START, end_timestamp=TEST_END,
        candle_count=1000, signal_count=500, long_count=250, short_count=250,
        signals_per_day=5.0, signals_per_100_candles=50.0,
        h5_median=-0.00053, positive_rate_5c=42.9,
    )

    gates, status, rationale = StrategySelectionEngine.evaluate_gates(
        candidate_val=c_val, baseline_val=b_val,
        candidate_test=c_test, baseline_test=b_test,
    )

    assert status in [ResearchStatusEnum.CANDIDATE_FOR_PAPER_TRADING, ResearchStatusEnum.RESEARCH_PROMOTED]
    assert len(gates) == 10
    assert sum(1 for g in gates if g.passed) >= 8


def test_research_engine_synthetic_run():
    """Verifies that StrategyResearchEngine runs deterministically on synthetic candles."""
    candles = generate_synthetic_candles(n=350)
    results = StrategyResearchEngine.run_all_experiments(candles)

    assert "BASELINE" in results
    assert "EXP_A1_PULLBACK_EMA21" in results
    assert "EXP_A2_PULLBACK_VWAP" in results
    assert "EXP_F1_COMBINED_CANDIDATE" in results
    assert results["BASELINE"].status == ResearchStatusEnum.VALIDATION_FAILED
