import asyncio
import pytest
from app.data.ws_manager import ResilientBinanceWebSocketManager
from app.data.schema import ConnectionStateEnum, Candle, CandleStateEnum, KlineStreamPayload


@pytest.mark.asyncio
async def test_ws_manager_subscriber_registration():
    mgr = ResilientBinanceWebSocketManager()
    queue = await mgr.register_subscriber("BTCUSDT", "15m")
    
    assert "BTCUSDT@15m" in mgr._subscribers
    assert queue in mgr._subscribers["BTCUSDT@15m"]

    # Test broadcasting a candle payload
    sample_candle = Candle(
        timestamp=1700000000000,
        open=60000.0,
        high=60500.0,
        low=59800.0,
        close=60200.0,
        volume=50.0,
        is_closed=False,
        state=CandleStateEnum.UPDATING,
    )
    payload = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "candle": sample_candle.model_dump(),
        "candle_state": "UPDATING",
        "server_time": 1700000005000,
    }

    await mgr._broadcast("BTCUSDT", "15m", payload)
    
    # Receive from queue
    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received["symbol"] == "BTCUSDT"
    assert received["candle"]["close"] == 60200.0

    # Test unregister
    await mgr.unregister_subscriber("BTCUSDT", "15m", queue)
    assert queue not in mgr._subscribers["BTCUSDT@15m"]

    await mgr.stop()


def test_ws_manager_initial_offline_status():
    mgr = ResilientBinanceWebSocketManager()
    status = mgr.get_status("BTCUSDT", "15m")
    assert status.state == ConnectionStateEnum.OFFLINE
    assert status.symbol == "BTCUSDT"
    assert status.timeframe == "15m"
