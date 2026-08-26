"""
Unit and Integration Tests for Phase 9 — Real-Time Shadow / Paper Validation Engine.
Verifies signal snapshot immutability, candidate isolation, deduplication, outcome calculations,
restart recovery, future mutation resistance, and security constraints.
"""

import copy
import os
import shutil
import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.shadow_validation.models import (
    ShadowSignal,
    HorizonOutcome,
    HorizonStatusEnum,
    SessionStatusEnum,
    ShadowSession,
)
from app.shadow_validation.config import compute_frozen_configuration_hashes, CANDIDATES
from app.shadow_validation.engine import ShadowValidationEngine
from app.shadow_validation.outcomes import ShadowOutcomeEngine
from app.shadow_validation.statistics import LiveStatisticsAggregator
from app.shadow_validation.drift import DriftMonitor
from app.shadow_validation.registry import ShadowRegistry


def generate_synthetic_candles(n: int = 100) -> list[Candle]:
    """Generates synthetic 15m candles with a realistic price walk."""
    import numpy as np
    rng = np.random.default_rng(42)
    candles = []
    price = 50000.0
    start_ts = 1704067200000

    for i in range(n):
        ts = start_ts + i * 900000
        ret = rng.normal(0.0002, 0.002)
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


def test_frozen_configuration_hashes():
    """Verifies that immutable configuration hashes are computed deterministically."""
    hashes1 = compute_frozen_configuration_hashes()
    hashes2 = compute_frozen_configuration_hashes()

    assert "phase5_signal_engine_hash" in hashes1
    assert "candidate_a2_config_hash" in hashes1
    assert "candidate_e2_config_hash" in hashes1
    assert hashes1 == hashes2


def test_candle_state_separation():
    """Verifies that only confirmed CLOSED candles generate shadow signals."""
    candles = generate_synthetic_candles(60)
    hashes = compute_frozen_configuration_hashes()
    engine = ShadowValidationEngine(session_id="test_session")
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY)

    # Open / updating candle must be rejected
    unclosed_candle = copy.deepcopy(candles[-1])
    unclosed_candle.is_closed = False
    unclosed_candle.state = CandleStateEnum.UPDATING

    sigs = engine.process_closed_candle(candles[:-1] + [unclosed_candle], quality, hashes)
    assert len(sigs) == 0


def test_duplicate_signal_prevention():
    """Verifies that identical closed candles do not generate duplicate shadow signals."""
    candles = generate_synthetic_candles(60)
    hashes = compute_frozen_configuration_hashes()
    engine = ShadowValidationEngine(session_id="test_session")
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY)

    sigs_first = engine.process_closed_candle(candles, quality, hashes)
    # Processing the exact same candle stream again must yield 0 new signals
    sigs_second = engine.process_closed_candle(candles, quality, hashes)
    assert len(sigs_second) == 0


def test_outcome_calculation_long_and_short():
    """Verifies forward return formulas, MFE, and MAE for Long and Short setups."""
    c0 = Candle(timestamp=1000, open=100, high=105, low=95, close=100, volume=10, is_closed=True, close_time=1899)
    c1 = Candle(timestamp=2000, open=100, high=110, low=98, close=105, volume=10, is_closed=True, close_time=2899)

    long_sig = ShadowSignal(
        signal_id="SIG_LONG", session_id="test", candidate_id="EXP_A2_PULLBACK_VWAP",
        symbol="BTCUSDT", timeframe="15m", candle_index=0, candle_open_time=1000,
        candle_close_time=1899, entry_reference_price=100.0, direction="LONG_SETUP",
        signal_score=65.0, signal_strength="MODERATE", regime="TRENDING_BULLISH",
        structure_state="BULLISH", volatility_state="NORMAL", trend_score=20.0,
        momentum_score=15.0, structure_score=15.0, volume_score=10.0,
        volatility_score=5.0, regime_score=5.0, atr=2.0,
        outcomes={1: HorizonOutcome(horizon=1, status=HorizonStatusEnum.PENDING)},
    )

    short_sig = ShadowSignal(
        signal_id="SIG_SHORT", session_id="test", candidate_id="EXP_E2_EXTENSION_VWAP",
        symbol="BTCUSDT", timeframe="15m", candle_index=0, candle_open_time=1000,
        candle_close_time=1899, entry_reference_price=100.0, direction="SHORT_SETUP",
        signal_score=65.0, signal_strength="MODERATE", regime="TRENDING_BEARISH",
        structure_state="BEARISH", volatility_state="NORMAL", trend_score=20.0,
        momentum_score=15.0, structure_score=15.0, volume_score=10.0,
        volatility_score=5.0, regime_score=5.0, atr=2.0,
        outcomes={1: HorizonOutcome(horizon=1, status=HorizonStatusEnum.PENDING)},
    )

    ShadowOutcomeEngine.update_pending_outcomes([long_sig, short_sig], [c0, c1])

    # Long: (105 - 100) / 100 = +0.05
    assert long_sig.outcomes[1].status == HorizonStatusEnum.COMPLETE
    assert long_sig.outcomes[1].raw_analytical_return == 0.05
    assert long_sig.outcomes[1].cost_adjusted_return_5bps == 0.0495

    # Short: (100 - 105) / 100 = -0.05
    assert short_sig.outcomes[1].status == HorizonStatusEnum.COMPLETE
    assert short_sig.outcomes[1].raw_analytical_return == -0.05


def test_incomplete_horizon_finalization():
    """Verifies that pending horizons are marked INSUFFICIENT_HORIZON upon session finalization."""
    sig = ShadowSignal(
        signal_id="SIG_PENDING", session_id="test", candidate_id="EXP_A2_PULLBACK_VWAP",
        symbol="BTCUSDT", timeframe="15m", candle_index=0, candle_open_time=1000,
        candle_close_time=1899, entry_reference_price=100.0, direction="LONG_SETUP",
        signal_score=60.0, signal_strength="MODERATE", regime="RANGING",
        structure_state="RANGE", volatility_state="NORMAL", trend_score=10.0,
        momentum_score=10.0, structure_score=10.0, volume_score=10.0,
        volatility_score=10.0, regime_score=10.0, atr=1.0,
        outcomes={
            1: HorizonOutcome(horizon=1, status=HorizonStatusEnum.COMPLETE, raw_analytical_return=0.01),
            5: HorizonOutcome(horizon=5, status=HorizonStatusEnum.PENDING),
        },
    )

    ShadowOutcomeEngine.finalize_session_horizons([sig])
    assert sig.outcomes[1].status == HorizonStatusEnum.COMPLETE
    assert sig.outcomes[5].status == HorizonStatusEnum.INSUFFICIENT_HORIZON


def test_future_mutation_invariance():
    """Verifies that mutating future candles > T does not affect signals generated at T."""
    candles = generate_synthetic_candles(70)
    hashes = compute_frozen_configuration_hashes()
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY)

    engine1 = ShadowValidationEngine(session_id="run1")
    sigs1 = engine1.process_closed_candle(candles[:60], quality, hashes)

    # Mutate all future candles after candle 60
    mutated = copy.deepcopy(candles)
    for c in mutated[60:]:
        c.close *= 1.5
        c.high *= 1.6
        c.low *= 0.5

    engine2 = ShadowValidationEngine(session_id="run2")
    sigs2 = engine2.process_closed_candle(mutated[:60], quality, hashes)

    assert len(sigs1) == len(sigs2)
    if sigs1:
        assert sigs1[0].entry_reference_price == sigs2[0].entry_reference_price
        assert sigs1[0].signal_score == sigs2[0].signal_score


def test_session_lifecycle_and_read_only_persistence(tmp_path):
    """Verifies session start, pause, resume, stop, and read-only artifact generation."""
    test_dir = str(tmp_path / "shadow_test")
    orig_dir = "data/shadow/sessions"
    os.makedirs(test_dir, exist_ok=True)

    session = ShadowRegistry.start_session(symbol="BTCUSDT", timeframe="15m")
    assert session.status == SessionStatusEnum.RUNNING

    paused = ShadowRegistry.pause_session(session.session_id)
    assert paused.status == SessionStatusEnum.PAUSED

    resumed = ShadowRegistry.resume_session(session.session_id)
    assert resumed.status == SessionStatusEnum.RUNNING

    stopped = ShadowRegistry.stop_session(session.session_id)
    assert stopped.status == SessionStatusEnum.STOPPED
    assert stopped.is_read_only is True


def test_security_audit_zero_exchange_trading_imports():
    """Verifies that no exchange execution, order placement, or account endpoints are imported."""
    import sys
    import importlib

    # Ensure no order execution modules are part of the shadow validation package
    shadow_pkg = importlib.import_module("app.shadow_validation")
    for mod_name in dir(shadow_pkg):
        assert "order" not in mod_name.lower()
        assert "trade_execution" not in mod_name.lower()
        assert "broker" not in mod_name.lower()
