import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.data.schema import Candle, CandleStateEnum


def create_candle(ts: int, c: float) -> Candle:
    return Candle(
        timestamp=ts,
        open=c - 10.0,
        high=c + 20.0,
        low=c - 20.0,
        close=c,
        volume=100.0,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )


@pytest.fixture
def mock_candles():
    base_ts = 1700000000000
    return [create_candle(base_ts + i * 900000, 60000.0 + (i * 20.0)) for i in range(100)]


def test_get_regime_endpoint(mock_candles):
    client = TestClient(app)
    with patch(
        "app.data.binance.BinanceMarketDataProvider.get_historical_klines",
        new=AsyncMock(return_value=mock_candles),
    ):
        response = client.get("/api/v1/analysis/regime?symbol=BTCUSDT&timeframe=15m")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "15m"
        assert "confirmed_snapshot" in data
        regime = data["confirmed_snapshot"]
        assert regime["direction"] in ["BULLISH", "BEARISH", "RANGE", "UNCERTAIN"]
        assert regime["trend_strength"] in ["NONE", "WEAK", "MODERATE", "STRONG", "VERY_STRONG"]
        assert regime["volatility_state"] in ["VERY_LOW", "LOW", "NORMAL", "HIGH", "EXTREME"]
        assert "overall_regime" in regime
        assert "evidence_strength" in regime


def test_get_structure_endpoint(mock_candles):
    client = TestClient(app)
    with patch(
        "app.data.binance.BinanceMarketDataProvider.get_historical_klines",
        new=AsyncMock(return_value=mock_candles),
    ):
        response = client.get("/api/v1/analysis/structure?symbol=BTCUSDT&timeframe=15m")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "15m"
        assert "confirmed_snapshot" in data
        struct = data["confirmed_snapshot"]
        assert "structure_direction" in struct
        assert "confirmed_swings" in struct
        assert "bos_events" in struct
        assert "support_zones" in struct
        assert "resistance_zones" in struct


def test_get_regime_history_endpoint(mock_candles):
    client = TestClient(app)
    with patch(
        "app.data.binance.BinanceMarketDataProvider.get_historical_klines",
        new=AsyncMock(return_value=mock_candles),
    ):
        response = client.get("/api/v1/analysis/regime/history?symbol=BTCUSDT&timeframe=15m&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
