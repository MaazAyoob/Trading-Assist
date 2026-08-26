import asyncio
import os
import pytest
from app.core.config import settings
from app.data.ws_manager import (
    ResilientBinanceWebSocketManager,
    build_ws_stream_url,
    _is_http_451_error,
)
from app.data.schema import ConnectionStateEnum, Candle, CandleStateEnum, MarketConnectionStatus


def test_ws_manager_default_endpoint():
    """Verify default WebSocket host is Binance's dedicated public market-data endpoint."""
    mgr = ResilientBinanceWebSocketManager()
    assert "data-stream.binance.vision" in mgr.base_ws_url
    assert settings.BINANCE_WS_BASE_URL == "wss://data-stream.binance.vision"


def test_ws_manager_configurable_endpoint():
    """Verify WebSocket host can be configured independently."""
    custom_url = "wss://custom-stream.binance.vision"
    mgr = ResilientBinanceWebSocketManager(base_ws_url=custom_url)
    assert mgr.base_ws_url == custom_url

    built_url = build_ws_stream_url(custom_url, "BTCUSDT", "15m")
    assert built_url == "wss://custom-stream.binance.vision/ws/btcusdt@kline_15m/btcusdt@ticker"


def test_build_ws_stream_url_variations():
    """Verify canonical Binance stream URL construction across formats."""
    # Standard base without trailing slash
    url1 = build_ws_stream_url("wss://data-stream.binance.vision", "BTCUSDT", "15m")
    assert url1 == "wss://data-stream.binance.vision/ws/btcusdt@kline_15m/btcusdt@ticker"

    # Base with trailing /ws
    url2 = build_ws_stream_url("wss://data-stream.binance.vision/ws", "BTCUSDT", "1m")
    assert url2 == "wss://data-stream.binance.vision/ws/btcusdt@kline_1m/btcusdt@ticker"

    # Base with /stream
    url3 = build_ws_stream_url("wss://data-stream.binance.vision/stream", "ETHUSDT", "1h")
    assert url3 == "wss://data-stream.binance.vision/stream?streams=ethusdt@kline_1h/ethusdt@ticker"


def test_no_trading_execution_imports():
    """Ensure data layer contains zero broker, order execution, or account API functionality."""
    import app.data.ws_manager as ws_mod
    import app.data.binance as binance_mod

    forbidden_keywords = ["place_order", "create_order", "cancel_order", "execute_trade", "account_balance", "api_secret_signature"]
    for mod in (ws_mod, binance_mod):
        mod_src = open(mod.__file__, "r", encoding="utf-8").read()
        for kw in forbidden_keywords:
            assert kw not in mod_src, f"Forbidden trading execution keyword '{kw}' found in {mod.__file__}"


def test_http_451_detection():
    """Verify HTTP 451 / geographic rejection detection helper."""
    assert _is_http_451_error(Exception("server rejected WebSocket connection: HTTP 451")) is True
    assert _is_http_451_error(Exception("HTTP 451 Unavailable For Legal Reasons")) is True
    assert _is_http_451_error(Exception("HTTP 403 Forbidden")) is True
    assert _is_http_451_error(Exception("Connection reset by peer")) is False


@pytest.mark.asyncio
async def test_ws_manager_subscriber_registration_and_broadcast():
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


@pytest.mark.asyncio
async def test_candle_deduplication_and_closed_detection():
    mgr = ResilientBinanceWebSocketManager()
    status = MarketConnectionStatus(
        state=ConnectionStateEnum.LIVE,
        symbol="BTCUSDT",
        timeframe="15m",
        last_ping=1700000000000,
        last_message_time=1700000000000,
        reconnect_attempts=0,
        message="Test",
    )

    # In-memory history with initial candles
    mgr._candle_histories["BTCUSDT@15m"] = [
        Candle(
            timestamp=1700000000000 + i * 900000,
            open=60000.0 + i,
            high=60100.0 + i,
            low=59900.0 + i,
            close=60050.0 + i,
            volume=10.0,
            close_time=1700000000000 + (i + 1) * 900000 - 1,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        for i in range(35)
    ]

    # Push a live updating tick with same timestamp as last candle
    current_ts = mgr._candle_histories["BTCUSDT@15m"][-1].timestamp
    tick = Candle(
        timestamp=current_ts,
        open=60034.0,
        high=60200.0,
        low=59900.0,
        close=60150.0,
        volume=15.0,
        close_time=current_ts + 900000 - 1,
        is_closed=False,
        state=CandleStateEnum.UPDATING,
    )

    await mgr._handle_candle_update(
        candle=tick,
        is_final_closed=False,
        event_time=1700032000000,
        symbol="BTCUSDT",
        timeframe="15m",
        status=status,
    )

    # Verify history length remained 35 (deduplicated / updated in-place)
    assert len(mgr._candle_histories["BTCUSDT@15m"]) == 35
    assert mgr._candle_histories["BTCUSDT@15m"][-1].close == 60150.0

    # Push a newly closed candle with next timestamp
    next_candle = Candle(
        timestamp=current_ts + 900000,
        open=60150.0,
        high=60300.0,
        low=60100.0,
        close=60250.0,
        volume=25.0,
        close_time=current_ts + 1800000 - 1,
        is_closed=True,
        state=CandleStateEnum.CLOSED,
    )

    await mgr._handle_candle_update(
        candle=next_candle,
        is_final_closed=True,
        event_time=1700032900000,
        symbol="BTCUSDT",
        timeframe="15m",
        status=status,
    )

    # History length increased to 36 with new closed candle
    assert len(mgr._candle_histories["BTCUSDT@15m"]) == 36
    assert mgr._latest_candles["BTCUSDT@15m"].is_closed is True
    assert mgr.get_confirmed_snapshot("BTCUSDT", "15m") is not None

    await mgr.stop()
