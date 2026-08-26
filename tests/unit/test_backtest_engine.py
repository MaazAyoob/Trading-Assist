import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from app.main import app
from app.backtesting.engine import BacktestEngine
from app.backtesting.config import BacktestConfig
from tests.unit.test_signal_engine import create_clear_bullish_swings


def test_backtest_engine_execution_and_integrity_report():
    candles = create_clear_bullish_swings(15)
    config = BacktestConfig(symbol="BTCUSDT", timeframe="15m", warmup_bars=40)

    run = BacktestEngine.run(candles, config=config)

    assert run.status == "COMPLETED"
    assert run.metrics.total_candles == len(candles)
    assert len(run.signal_outcomes) > 0
    assert run.integrity_report.checks_passed is True
    assert run.integrity_report.future_leakage_detected is False
    assert run.integrity_report.causal_processing is True
    assert run.integrity_report.signal_immutability_verified is True


@pytest.mark.asyncio
async def test_backtest_api_endpoints():
    from app.db.session import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Trigger Backtest Run
        payload = {
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "candle_count": 100,
            "warmup_bars": 40,
            "horizons": [1, 3, 5],
        }
        res_post = await ac.post("/api/v1/backtesting/run", json=payload)
        assert res_post.status_code == 200
        run_data = res_post.json()
        run_id = run_data["run_id"]
        assert run_data["status"] == "COMPLETED"
        assert "metrics" in run_data
        assert "integrity_report" in run_data

        # 2. List Runs
        res_list = await ac.get("/api/v1/backtesting/runs?symbol=BTCUSDT")
        assert res_list.status_code == 200
        runs = res_list.json()
        assert len(runs) >= 1
        assert any(r["run_id"] == run_id for r in runs)

        # 3. Get Single Run
        res_get = await ac.get(f"/api/v1/backtesting/runs/{run_id}")
        assert res_get.status_code == 200
        assert res_get.json()["run_id"] == run_id

        # 4. Get Metrics
        res_metrics = await ac.get(f"/api/v1/backtesting/runs/{run_id}/metrics")
        assert res_metrics.status_code == 200
        assert "horizon_metrics" in res_metrics.json()

        # 5. Get Signals
        res_signals = await ac.get(f"/api/v1/backtesting/runs/{run_id}/signals")
        assert res_signals.status_code == 200
        assert isinstance(res_signals.json(), list)
