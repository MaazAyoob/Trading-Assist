import sys
import os
import pytest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from app.backtesting.engine import BacktestEngine
from app.backtesting.config import BacktestConfig
from tests.unit.test_signal_engine import create_clear_bullish_swings


def test_backtest_reproducibility_run_a_vs_run_b():
    candles = create_clear_bullish_swings(12)
    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", warmup_bars=40)

    run_a = BacktestEngine.run(candles, config=config)
    run_b = BacktestEngine.run(candles, config=config)

    assert len(run_a.signal_outcomes) == len(run_b.signal_outcomes)
    assert run_a.metrics.total_signals == run_b.metrics.total_signals
    assert run_a.dataset_metadata.sha256_hash == run_b.dataset_metadata.sha256_hash

    for s_a, s_b in zip(run_a.signal_outcomes, run_b.signal_outcomes):
        assert s_a.signal_timestamp == s_b.signal_timestamp
        assert s_a.signal_direction == s_b.signal_direction
        assert s_a.signal_score == s_b.signal_score
        assert s_a.entry_reference_price == s_b.entry_reference_price
        for h in config.horizons:
            out_a = s_a.outcomes.get(h)
            out_b = s_b.outcomes.get(h)
            assert out_a.forward_return == out_b.forward_return
            assert out_a.mfe == out_b.mfe
            assert out_a.mae == out_b.mae
            assert out_a.status == out_b.status
