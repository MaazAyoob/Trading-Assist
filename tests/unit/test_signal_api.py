import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_signal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analysis/signal?symbol=BTCUSDT&timeframe=15m")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["timeframe"] == "15m"
        assert "confirmed_signal" in data
        assert "direction" in data["confirmed_signal"]
        assert "score" in data["confirmed_signal"]
        assert "score_trace" in data["confirmed_signal"]
        assert "disclaimer" in data["confirmed_signal"]


@pytest.mark.asyncio
async def test_get_signal_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analysis/signal/history?symbol=BTCUSDT&timeframe=15m&limit=15")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "direction" in data[0]
            assert "score_trace" in data[0]


@pytest.mark.asyncio
async def test_explain_signal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analysis/signal/explain?symbol=BTCUSDT&timeframe=15m")
        assert response.status_code == 200
        data = response.json()
        assert "evidence_groups" in data
        assert "TREND" in data["evidence_groups"]
        assert "MOMENTUM" in data["evidence_groups"]
        assert "STRUCTURE" in data["evidence_groups"]
        assert "VOLUME" in data["evidence_groups"]
        assert "score_trace" in data
