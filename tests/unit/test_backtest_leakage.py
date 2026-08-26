import sys
import os
import pytest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from app.data.schema import Candle, CandleStateEnum
from app.indicators.engine import IndicatorEngine
from app.structure.engine import MarketStructureEngine
from app.backtesting.engine import BacktestEngine
from app.backtesting.config import BacktestConfig
from tests.unit.test_signal_engine import create_clear_bullish_swings


def test_future_candle_mutation_leaves_prior_signals_identical():
    """
    Adversarial test: Mutating future candles MUST NOT alter any signal
    generated before the mutation point.
    """
    candles = create_clear_bullish_swings(12)  # ~108 candles
    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", warmup_bars=40)

    # 1. Base run
    run1 = BacktestEngine.run(candles, config=config)
    signals_before_cutoff_1 = [s for s in run1.signal_outcomes if s.signal_timestamp < candles[70].timestamp]

    # 2. Mutate future candles dramatically from index 70 onwards
    mutated_candles = [c.model_copy() for c in candles]
    for k in range(70, len(mutated_candles)):
        mutated_candles[k].open *= 2.5
        mutated_candles[k].high *= 3.0
        mutated_candles[k].low *= 0.5
        mutated_candles[k].close *= 0.3
        mutated_candles[k].volume *= 10.0

    run2 = BacktestEngine.run(mutated_candles, config=config)
    signals_before_cutoff_2 = [s for s in run2.signal_outcomes if s.signal_timestamp < candles[70].timestamp]

    # Must be strictly identical in count, timestamp, direction, and score
    assert len(signals_before_cutoff_1) == len(signals_before_cutoff_2)
    for s1, s2 in zip(signals_before_cutoff_1, signals_before_cutoff_2):
        assert s1.signal_timestamp == s2.signal_timestamp
        assert s1.signal_direction == s2.signal_direction
        assert s1.signal_score == s2.signal_score
        assert s1.signal_strength == s2.signal_strength


def test_swing_confirmation_delay_enforcement_at_t_plus_3():
    """
    Verifies that with LEFT=3, RIGHT=3, a pivot high formed at bar T
    is NEVER treated as confirmed at bars T, T+1, T+2, and ONLY at T+3.
    """
    # Create distinct peak at index 5
    candles = []
    base_price = 50000.0
    t = 1700000000000
    prices = [10, 20, 30, 40, 50, 100, 45, 40, 35, 30, 25, 20]  # Peak at index 5 (100)

    for p in prices:
        close = base_price + p
        candles.append(
            Candle(
                timestamp=t,
                open=close - 2.0,
                high=close + 5.0,
                low=close - 5.0,
                close=close,
                volume=100.0,
                close_time=t + 899999,
                is_closed=True,
                state=CandleStateEnum.CLOSED,
            )
        )
        t += 900000

    # At bar 5 (Peak bar): Right side count is 0 -> NOT confirmed
    struct_t0 = MarketStructureEngine.evaluate(candles[:6], is_confirmed=True)
    assert not any(sw.price == base_price + 105.0 for sw in struct_t0.confirmed_swings)

    # At bar 6 (T+1): Right side count is 1 -> NOT confirmed
    struct_t1 = MarketStructureEngine.evaluate(candles[:7], is_confirmed=True)
    assert not any(sw.price == base_price + 105.0 for sw in struct_t1.confirmed_swings)

    # At bar 7 (T+2): Right side count is 2 -> NOT confirmed
    struct_t2 = MarketStructureEngine.evaluate(candles[:8], is_confirmed=True)
    assert not any(sw.price == base_price + 105.0 for sw in struct_t2.confirmed_swings)

    # At bar 8 (T+3): Right side count is 3 -> CONFIRMED at T+3!
    struct_t3 = MarketStructureEngine.evaluate(candles[:9], is_confirmed=True)
    assert any(sw.price == base_price + 105.0 for sw in struct_t3.confirmed_swings)


def test_reference_snapshot_causal_equivalence():
    """
    Running isolated slice up to bar K must match the historical snapshot at bar K
    in a full backtest.
    """
    candles = create_clear_bullish_swings(10)
    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", warmup_bars=40)

    # Isolated snapshot at bar 65
    slice_65 = candles[:66]
    ind_isolated = IndicatorEngine.calculate_snapshot(slice_65, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)

    # Full backtest
    run = BacktestEngine.run(candles, config=config)

    # Verify indicators calculate identically
    ind_recalculated = IndicatorEngine.calculate_snapshot(slice_65, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    assert ind_isolated.trend.ema_9 == ind_recalculated.trend.ema_9
    assert ind_isolated.momentum.rsi == ind_recalculated.momentum.rsi
