import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.data.schema import Candle, CandleStateEnum


def create_fake_candles(count=100):
    base_ts = 1700000000000
    return [
        Candle(
            timestamp=base_ts + i * 900000,
            open=50000.0 + i,
            high=50100.0 + i,
            low=49900.0 + i,
            close=50050.0 + i,
            volume=100.0,
            close_time=base_ts + (i + 1) * 900000 - 1,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        for i in range(count)
    ]


@pytest.mark.asyncio
async def test_get_indicators_endpoint(monkeypatch):
    class MockProvider:
        async def get_historical_klines(self, symbol, timeframe, limit=300, start_time=None, end_time=None):
            return create_fake_candles(100)
        async def close(self): pass

    from app.api.v1.endpoints import analysis
    monkeypatch.setattr(analysis, "get_market_provider", lambda: MockProvider())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analysis/indicators?symbol=BTCUSDT&timeframe=15m")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "15m"
        assert data["quality"]["status"] == "HEALTHY"
        assert data["confirmed_snapshot"]["trend"]["ema_9"] is not None
        assert data["realtime_snapshot"] is None


@pytest.mark.asyncio
async def test_get_indicators_history_endpoint(monkeypatch):
    class MockProvider:
        async def get_historical_klines(self, symbol, timeframe, limit=300, start_time=None, end_time=None):
            return create_fake_candles(100)
        async def close(self): pass

    from app.api.v1.endpoints import analysis
    monkeypatch.setattr(analysis, "get_market_provider", lambda: MockProvider())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analysis/indicators/history?symbol=BTCUSDT&timeframe=15m&limit=50")
        assert res.status_code == 200
        history = res.json()
        assert len(history) == 50
        assert history[-1]["close"] > 0
        assert history[-1]["ema_9"] is not None


@pytest.mark.asyncio
async def test_get_indicators_invalid_timeframe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analysis/indicators?symbol=BTCUSDT&timeframe=37m")
        assert res.status_code == 400
        assert "not supported" in res.json()["detail"]
