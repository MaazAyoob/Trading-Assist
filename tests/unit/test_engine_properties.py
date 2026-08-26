import copy
import json
import pytest
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.indicators.config import IndicatorConfig


def generate_candles(count: int = 250, start_ts: int = 1700000000000) -> list[Candle]:
    candles = []
    base_price = 50000.0
    for i in range(count):
        # Deterministic price oscillation
        delta = (i % 10) * 15.0 - 60.0
        c = base_price + delta
        h = c + 50.0
        l = c - 50.0
        o = c - 10.0
        v = 100.0 + (i % 5) * 20.0
        candles.append(
            Candle(
                timestamp=start_ts + i * 900000,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
                close_time=start_ts + (i + 1) * 900000 - 1,
                is_closed=True,
                state=CandleStateEnum.CLOSED,
            )
        )
    return candles


def test_immutability():
    """Verify IndicatorEngine does not mutate the input candle list or candle objects."""
    candles = generate_candles(100)
    original_copy = copy.deepcopy(candles)

    snap = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m")
    hist = IndicatorEngine.calculate_history(candles, "BTCUSDT", "15m")

    assert len(candles) == len(original_copy)
    for orig, curr in zip(original_copy, candles):
        assert orig.model_dump() == curr.model_dump()


def test_determinism():
    """Verify identical inputs produce strictly identical snapshots and history."""
    candles = generate_candles(100)

    snap1 = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m")
    snap2 = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m")

    assert snap1.model_dump() == snap2.model_dump()


def test_no_repainting():
    """
    Verify historical closed indicator values do NOT change when future candles are appended.
    """
    candles_t1 = generate_candles(150)
    snap_t1 = IndicatorEngine.calculate_snapshot(candles_t1, "BTCUSDT", "15m", is_confirmed=True)

    # Append 50 new closed candles
    candles_t2 = generate_candles(200)
    # Calculate history for full 200 bars
    hist_t2 = IndicatorEngine.calculate_history(candles_t2, "BTCUSDT", "15m", limit=200)

    # The point at index 149 in hist_t2 corresponds to the same closed bar as snap_t1
    t1_bar_in_history = hist_t2[149]

    assert t1_bar_in_history.timestamp == snap_t1.timestamp
    assert t1_bar_in_history.ema_9 == snap_t1.trend.ema_9
    assert t1_bar_in_history.ema_21 == snap_t1.trend.ema_21
    assert t1_bar_in_history.rsi == snap_t1.momentum.rsi
    assert t1_bar_in_history.macd == snap_t1.momentum.macd
    assert t1_bar_in_history.bb_upper == snap_t1.volatility.bb_upper


def test_versioning():
    """Verify generated snapshots contain version signatures."""
    candles = generate_candles(50)
    custom_cfg = IndicatorConfig(
        indicator_engine_version="0.3.0",
        indicator_config_version="test-2026-v1",
    )
    snap = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m", config=custom_cfg)
    assert snap.indicator_engine_version == "0.3.0"
    assert snap.indicator_config_version == "test-2026-v1"


def test_candle_state_separation():
    """Verify open/updating candles cannot produce confirmed snapshots."""
    candles = generate_candles(50)
    # Mark last candle as open/updating
    candles[-1].is_closed = False
    candles[-1].state = CandleStateEnum.UPDATING

    snap_confirmed = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m", is_confirmed=True)
    # Confirmed snapshot timestamp must be candle at index -2 (the last closed candle)
    assert snap_confirmed.timestamp == candles[-2].timestamp
    assert snap_confirmed.is_confirmed is True

    # Realtime snapshot includes the unconfirmed candle
    snap_realtime = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m", is_confirmed=False)
    assert snap_realtime.timestamp == candles[-1].timestamp
    assert snap_realtime.is_confirmed is False


def test_nan_infinity_policy():
    """Verify no NaN, Infinity, or -Infinity values escape JSON serialization."""
    candles = generate_candles(10)  # Under-warmed for EMA 200, MACD, etc.
    snap = IndicatorEngine.calculate_snapshot(candles, "BTCUSDT", "15m")

    # EMA 200 should be None (not NaN)
    assert snap.trend.ema_200 is None
    assert snap.trend.ema_9 is not None

    # Verify JSON serialization does not contain 'NaN' or 'Infinity'
    dump_str = snap.model_dump_json()
    assert "NaN" not in dump_str
    assert "Infinity" not in dump_str
    # Verify standard json parse succeeds
    parsed = json.loads(dump_str)
    assert parsed["trend"]["ema_200"] is None
