import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import logger
from app.data.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/market/{symbol}/{timeframe}")
async def websocket_market_feed(websocket: WebSocket, symbol: str, timeframe: str):
    """
    WebSocket endpoint for frontend streaming.
    Pushes live candlestick updates, candle state (OPEN, UPDATING, CLOSED),
    and realtime/confirmed indicator, regime, structure, and research signal snapshots.
    """
    symbol = symbol.upper()
    await websocket.accept()
    logger.info(f"Frontend WebSocket client connected for {symbol}@{timeframe}")

    queue = await ws_manager.register_subscriber(symbol, timeframe)

    try:
        latest_candle = ws_manager.get_latest_candle(symbol, timeframe)
        latest_ticker = ws_manager.get_latest_ticker(symbol)
        confirmed_ind = ws_manager.get_confirmed_snapshot(symbol, timeframe)
        realtime_ind = ws_manager.get_realtime_snapshot(symbol, timeframe)
        confirmed_regime = ws_manager.get_confirmed_regime(symbol, timeframe)
        realtime_regime = ws_manager.get_realtime_regime(symbol, timeframe)
        confirmed_struct = ws_manager.get_confirmed_structure(symbol, timeframe)
        realtime_struct = ws_manager.get_realtime_structure(symbol, timeframe)
        confirmed_signal = ws_manager.get_confirmed_signal(symbol, timeframe)
        realtime_signal = ws_manager.get_realtime_signal(symbol, timeframe)
        confirmed_decision = ws_manager.get_confirmed_decision(symbol, timeframe)
        realtime_decision = ws_manager.get_realtime_decision(symbol, timeframe)
        status = ws_manager.get_status(symbol, timeframe)

        await websocket.send_json({
            "type": "INITIAL_STATE",
            "symbol": symbol,
            "timeframe": timeframe,
            "status": status.model_dump(),
            "candle": latest_candle.model_dump() if latest_candle else None,
            "candle_state": latest_candle.state.value if latest_candle else "CLOSED",
            "ticker": latest_ticker.model_dump() if latest_ticker else None,
            "indicators": {
                "confirmed": confirmed_ind.model_dump() if confirmed_ind else None,
                "realtime": realtime_ind.model_dump() if realtime_ind else None,
            },
            "regime": {
                "confirmed": confirmed_regime.model_dump() if confirmed_regime else None,
                "realtime": realtime_regime.model_dump() if realtime_regime else None,
            },
            "structure": {
                "confirmed": confirmed_struct.model_dump() if confirmed_struct else None,
                "realtime": realtime_struct.model_dump() if realtime_struct else None,
            },
            "signal": {
                "confirmed": confirmed_signal.model_dump() if confirmed_signal else None,
                "realtime": realtime_signal.model_dump() if realtime_signal else None,
            },
            "trade_decision": {
                "confirmed": confirmed_decision.model_dump() if confirmed_decision else None,
                "realtime": realtime_decision.model_dump() if realtime_decision else None,
            },
        })

        while True:
            payload = await queue.get()
            if isinstance(payload, dict):
                await websocket.send_json(payload)
            else:
                await websocket.send_json(payload.model_dump())

    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.info(f"Frontend WebSocket client disconnected for {symbol}@{timeframe}")
    except Exception as e:
        logger.error(f"WebSocket client error ({symbol}@{timeframe}): {e}")
    finally:
        await ws_manager.unregister_subscriber(symbol, timeframe, queue)
