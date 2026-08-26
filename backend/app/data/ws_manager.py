import asyncio
import json
import time
from typing import Dict, Set, Optional, List
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode, WebSocketException
from app.core.config import settings
from app.core.logging import logger
from app.data.schema import (
    Candle,
    CandleStateEnum,
    ConnectionStateEnum,
    MarketConnectionStatus,
    KlineStreamPayload,
    Ticker,
    QualityStatusEnum,
)
from app.data.quality import MarketDataQualityValidator
from app.indicators.engine import IndicatorEngine
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot
from app.regime.engine import MarketRegimeEngine
from app.structure.models import MarketStructureSnapshot
from app.structure.engine import MarketStructureEngine
from app.signals.models import ResearchSignal
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.models import TradePlan
from app.trade_decision.engine import TradeDecisionEngine
from app.shadow_validation.registry import ShadowRegistry
from app.shadow_validation.engine import ShadowValidationEngine
from app.shadow_validation.outcomes import ShadowOutcomeEngine
from app.shadow_validation.models import SessionStatusEnum


def _is_http_451_error(exc: Exception) -> bool:
    """Check if error is an HTTP 451/403 geo-restriction response."""
    err_str = str(exc).lower()
    if "451" in err_str or "403" in err_str or "unavailable for legal reasons" in err_str:
        return True
    if isinstance(exc, InvalidStatusCode) and exc.status_code in (451, 403):
        return True
    return False


def build_ws_stream_url(base_ws_url: str, symbol: str, timeframe: str) -> str:
    """
    Construct canonical Binance WebSocket stream URL for a symbol and timeframe.
    Supports both standard base URLs and dedicated public market data domains (e.g. data-stream.binance.vision).
    """
    base = base_ws_url.rstrip("/")
    stream_name = f"{symbol.lower()}@kline_{timeframe}"
    ticker_stream = f"{symbol.lower()}@ticker"

    if base.endswith("/ws"):
        return f"{base}/{stream_name}/{ticker_stream}"
    elif "stream" in base and "?" in base:
        return f"{base}&streams={stream_name}/{ticker_stream}"
    elif base.endswith("/stream"):
        return f"{base}?streams={stream_name}/{ticker_stream}"
    else:
        return f"{base}/ws/{stream_name}/{ticker_stream}"


class ResilientBinanceWebSocketManager:
    """
    Robust WebSocket Manager for Binance market data streams.
    Handles:
    - Automatic exponential backoff reconnection
    - Ping/Pong heartbeat monitoring
    - Explicit candle lifecycle (OPEN, UPDATING, CLOSED)
    - Separation of Realtime vs Confirmed indicators, regimes, structures, signals, and trade decisions
    - Non-repainting historical state
    - Multi-subscriber pub/sub broadcasting to connected web clients
    - Safe REST fallback architecture if WebSocket encounters HTTP 451 or cloud restrictions
    """

    def __init__(self, base_ws_url: Optional[str] = None):
        self.base_ws_url = base_ws_url or settings.BINANCE_WS_BASE_URL
        self._running = False
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}  # key: "BTCUSDT@15m" -> set of Queues
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._latest_candles: Dict[str, Candle] = {}
        self._latest_tickers: Dict[str, Ticker] = {}
        self._candle_histories: Dict[str, List[Candle]] = {}  # In-memory clean history per symbol@tf
        self._latest_confirmed_snapshots: Dict[str, IndicatorSnapshot] = {}
        self._latest_realtime_snapshots: Dict[str, IndicatorSnapshot] = {}
        self._latest_confirmed_regimes: Dict[str, MarketRegimeSnapshot] = {}
        self._latest_realtime_regimes: Dict[str, MarketRegimeSnapshot] = {}
        self._latest_confirmed_structures: Dict[str, MarketStructureSnapshot] = {}
        self._latest_realtime_structures: Dict[str, MarketStructureSnapshot] = {}
        self._latest_confirmed_signals: Dict[str, ResearchSignal] = {}
        self._latest_realtime_signals: Dict[str, ResearchSignal] = {}
        self._latest_confirmed_decisions: Dict[str, TradePlan] = {}
        self._latest_realtime_decisions: Dict[str, TradePlan] = {}
        self._connection_states: Dict[str, MarketConnectionStatus] = {}
        self._last_event_times: Dict[str, int] = {}

    def get_status(self, symbol: str, timeframe: str) -> MarketConnectionStatus:
        key = f"{symbol.upper()}@{timeframe}"
        if key in self._connection_states:
            return self._connection_states[key]
        return MarketConnectionStatus(
            state=ConnectionStateEnum.OFFLINE,
            symbol=symbol.upper(),
            timeframe=timeframe,
            last_ping=int(time.time() * 1000),
            last_message_time=0,
            reconnect_attempts=0,
            message="Stream not initiated",
        )

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        return self._latest_candles.get(f"{symbol.upper()}@{timeframe}")

    def get_latest_ticker(self, symbol: str) -> Optional[Ticker]:
        return self._latest_tickers.get(symbol.upper())

    def get_confirmed_snapshot(self, symbol: str, timeframe: str) -> Optional[IndicatorSnapshot]:
        return self._latest_confirmed_snapshots.get(f"{symbol.upper()}@{timeframe}")

    def get_realtime_snapshot(self, symbol: str, timeframe: str) -> Optional[IndicatorSnapshot]:
        return self._latest_realtime_snapshots.get(f"{symbol.upper()}@{timeframe}")

    def get_confirmed_regime(self, symbol: str, timeframe: str) -> Optional[MarketRegimeSnapshot]:
        return self._latest_confirmed_regimes.get(f"{symbol.upper()}@{timeframe}")

    def get_realtime_regime(self, symbol: str, timeframe: str) -> Optional[MarketRegimeSnapshot]:
        return self._latest_realtime_regimes.get(f"{symbol.upper()}@{timeframe}")

    def get_confirmed_structure(self, symbol: str, timeframe: str) -> Optional[MarketStructureSnapshot]:
        return self._latest_confirmed_structures.get(f"{symbol.upper()}@{timeframe}")

    def get_realtime_structure(self, symbol: str, timeframe: str) -> Optional[MarketStructureSnapshot]:
        return self._latest_realtime_structures.get(f"{symbol.upper()}@{timeframe}")

    def get_confirmed_signal(self, symbol: str, timeframe: str) -> Optional[ResearchSignal]:
        return self._latest_confirmed_signals.get(f"{symbol.upper()}@{timeframe}")

    def get_realtime_signal(self, symbol: str, timeframe: str) -> Optional[ResearchSignal]:
        return self._latest_realtime_signals.get(f"{symbol.upper()}@{timeframe}")

    def get_confirmed_decision(self, symbol: str, timeframe: str) -> Optional[TradePlan]:
        return self._latest_confirmed_decisions.get(f"{symbol.upper()}@{timeframe}")

    def get_realtime_decision(self, symbol: str, timeframe: str) -> Optional[TradePlan]:
        return self._latest_realtime_decisions.get(f"{symbol.upper()}@{timeframe}")

    async def register_subscriber(self, symbol: str, timeframe: str) -> asyncio.Queue:
        """Register a client queue to receive live updates for symbol & timeframe."""
        key = f"{symbol.upper()}@{timeframe}"
        if key not in self._subscribers:
            self._subscribers[key] = set()
            self._ensure_stream_task(symbol, timeframe)

        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers[key].add(queue)
        logger.info(f"Registered subscriber for {key}. Total subscribers: {len(self._subscribers[key])}")
        return queue

    async def unregister_subscriber(self, symbol: str, timeframe: str, queue: asyncio.Queue):
        key = f"{symbol.upper()}@{timeframe}"
        if key in self._subscribers and queue in self._subscribers[key]:
            self._subscribers[key].remove(queue)
            logger.info(f"Unregistered subscriber for {key}. Remaining: {len(self._subscribers[key])}")

    def _ensure_stream_task(self, symbol: str, timeframe: str):
        key = f"{symbol.upper()}@{timeframe}"
        if key not in self._active_tasks or self._active_tasks[key].done():
            self._active_tasks[key] = asyncio.create_task(
                self._stream_worker(symbol.upper(), timeframe)
            )

    async def _broadcast(self, symbol: str, timeframe: str, payload: dict):
        key = f"{symbol.upper()}@{timeframe}"
        if key in self._subscribers:
            dead_queues = set()
            for q in self._subscribers[key]:
                try:
                    if q.full():
                        try:
                            q.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    q.put_nowait(payload)
                except Exception:
                    dead_queues.add(q)
            for dead_q in dead_queues:
                self._subscribers[key].discard(dead_q)

    async def _handle_candle_update(
        self,
        candle: Candle,
        is_final_closed: bool,
        event_time: int,
        symbol: str,
        timeframe: str,
        status: MarketConnectionStatus,
    ):
        """Process an updated or finalized candle, compute analytical snapshots, and broadcast."""
        key = f"{symbol}@{timeframe}"
        now_ms = int(time.time() * 1000)

        # Validate single candle
        is_valid, errs = MarketDataQualityValidator.validate_candle(candle)
        if not is_valid:
            logger.warning(f"[{key}] Dropping invalid candle: {errs}")
            return

        candle_state = CandleStateEnum.CLOSED if is_final_closed else CandleStateEnum.UPDATING
        candle.state = candle_state
        candle.is_closed = is_final_closed

        self._latest_candles[key] = candle
        if key not in self._candle_histories:
            self._candle_histories[key] = []
        history = self._candle_histories[key]

        # Update in-memory rolling candle list
        if not history:
            history.append(candle)
        else:
            if history[-1].timestamp == candle.timestamp:
                history[-1] = candle
            elif candle.timestamp > history[-1].timestamp:
                history.append(candle)
                if len(history) > 500:
                    history.pop(0)

        # 1. Calculate Realtime Indicators, Structure, Regime, Signals, and Trade Decisions
        realtime_snap = IndicatorEngine.calculate_snapshot(
            history,
            symbol=symbol,
            timeframe=timeframe,
            is_confirmed=False,
            quality_status=QualityStatusEnum.HEALTHY,
        )
        self._latest_realtime_snapshots[key] = realtime_snap

        realtime_struct = MarketStructureEngine.evaluate(
            history,
            indicators=realtime_snap,
            is_confirmed=False,
        )
        self._latest_realtime_structures[key] = realtime_struct

        realtime_regime = MarketRegimeEngine.classify(
            candles=history,
            indicators=realtime_snap,
            structure_state=realtime_struct.structure_direction,
            is_confirmed=False,
        )
        self._latest_realtime_regimes[key] = realtime_regime

        realtime_signal = MultiFactorSignalEngine.calculate_signal(
            candles=history,
            indicators=realtime_snap,
            regime=realtime_regime,
            structure=realtime_struct,
            is_confirmed=False,
        )
        self._latest_realtime_signals[key] = realtime_signal

        realtime_decision = TradeDecisionEngine.calculate_decision(
            candles=history,
            indicators=realtime_snap,
            regime=realtime_regime,
            structure=realtime_struct,
            signal=realtime_signal,
            strategy_context_id="EXP_A2_PULLBACK_VWAP",
            is_confirmed=False,
        )
        self._latest_realtime_decisions[key] = realtime_decision

        # 2. If candle interval is finalized/closed, calculate Confirmed States
        if is_final_closed:
            confirmed_snap = IndicatorEngine.calculate_snapshot(
                history,
                symbol=symbol,
                timeframe=timeframe,
                is_confirmed=True,
                quality_status=QualityStatusEnum.HEALTHY,
            )
            self._latest_confirmed_snapshots[key] = confirmed_snap

            confirmed_struct = MarketStructureEngine.evaluate(
                history,
                indicators=confirmed_snap,
                is_confirmed=True,
            )
            self._latest_confirmed_structures[key] = confirmed_struct

            confirmed_regime = MarketRegimeEngine.classify(
                candles=history,
                indicators=confirmed_snap,
                structure_state=confirmed_struct.structure_direction,
                is_confirmed=True,
            )
            self._latest_confirmed_regimes[key] = confirmed_regime

            confirmed_signal = MultiFactorSignalEngine.calculate_signal(
                candles=history,
                indicators=confirmed_snap,
                regime=confirmed_regime,
                structure=confirmed_struct,
                is_confirmed=True,
            )
            self._latest_confirmed_signals[key] = confirmed_signal

            confirmed_decision = TradeDecisionEngine.calculate_decision(
                candles=history,
                indicators=confirmed_snap,
                regime=confirmed_regime,
                structure=confirmed_struct,
                signal=confirmed_signal,
                strategy_context_id="EXP_A2_PULLBACK_VWAP",
                is_confirmed=True,
            )
            self._latest_confirmed_decisions[key] = confirmed_decision
            logger.debug(
                f"[{key}] Confirmed candle closed at {candle.timestamp}. "
                f"Decision: {confirmed_decision.decision.value} ({confirmed_decision.direction})"
            )

            # 3. Phase 9 Shadow Validation Pipeline (if session active)
            try:
                active_sess = ShadowRegistry.get_active_session()
                if active_sess and active_sess.status == SessionStatusEnum.RUNNING:
                    signals = ShadowRegistry.get_signals(active_sess.session_id)
                    ShadowOutcomeEngine.update_pending_outcomes(signals, history)

                    shadow_quality = MarketDataQualityValidator.validate_dataset(
                        candles=history,
                        symbol=symbol,
                        timeframe=timeframe,
                        is_confirmed=True,
                    )
                    shadow_engine = ShadowValidationEngine(session_id=active_sess.session_id)
                    new_shadow_sigs = shadow_engine.process_closed_candle(
                        candles=history,
                        quality=shadow_quality,
                        session_config_hashes=active_sess.configuration_hashes,
                        received_timestamp=now_ms,
                    )
                    if new_shadow_sigs:
                        ShadowRegistry.record_signals(new_shadow_sigs)
                    ShadowRegistry.update_candle_progress(candle.close_time)
            except Exception as shadow_err:
                logger.error(f"ShadowValidation error on closed candle: {shadow_err}")

        payload = {
            "type": "KLINE_UPDATE",
            "symbol": symbol,
            "timeframe": timeframe,
            "candle": candle.model_dump(),
            "candle_state": candle_state.value,
            "ticker": self._latest_tickers.get(symbol).model_dump() if self._latest_tickers.get(symbol) else None,
            "server_time": event_time,
            "status": self.get_status(symbol, timeframe).model_dump(),
            "indicators": {
                "realtime": realtime_snap.model_dump(),
                "confirmed": self._latest_confirmed_snapshots.get(key).model_dump() if self._latest_confirmed_snapshots.get(key) else None,
            },
            "regime": {
                "realtime": realtime_regime.model_dump(),
                "confirmed": self._latest_confirmed_regimes.get(key).model_dump() if self._latest_confirmed_regimes.get(key) else None,
            },
            "structure": {
                "realtime": realtime_struct.model_dump(),
                "confirmed": self._latest_confirmed_structures.get(key).model_dump() if self._latest_confirmed_structures.get(key) else None,
            },
            "signal": {
                "realtime": realtime_signal.model_dump(),
                "confirmed": self._latest_confirmed_signals.get(key).model_dump() if self._latest_confirmed_signals.get(key) else None,
            },
            "trade_decision": {
                "realtime": realtime_decision.model_dump() if realtime_decision else None,
                "confirmed": self._latest_confirmed_decisions.get(key).model_dump() if self._latest_confirmed_decisions.get(key) else None,
            },
        }

        await self._broadcast(symbol, timeframe, payload)

    async def _rest_polling_fallback(self, symbol: str, timeframe: str, status: MarketConnectionStatus):
        """
        Safe fallback architecture when WebSocket is rejected (e.g. HTTP 451 on Render).
        Polls Binance's public REST market-data endpoint periodically while keeping
        the exact same internal candle, indicator, signal, decision, and broadcast interfaces.
        """
        key = f"{symbol}@{timeframe}"
        logger.info(f"[Binance WS] Entering public REST market-data polling fallback for {key}")

        from app.data.binance import BinanceMarketDataProvider
        provider = BinanceMarketDataProvider()

        status.state = ConnectionStateEnum.LIVE
        status.message = "Connected (REST market data fallback active)"

        last_closed_ts = 0
        consecutive_errors = 0
        last_ws_retry_time = time.time()
        ws_probe_interval = 60.0  # Probe native WebSocket every 60s

        while self._running:
            try:
                now_ms = int(time.time() * 1000)
                status.last_ping = now_ms

                # 1. Warm up history if empty, else fetch recent klines
                limit = 100 if len(self._candle_histories.get(key, [])) < 30 else 5
                raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)

                # 2. Fetch 24hr ticker
                try:
                    ticker = await provider.get_ticker(symbol=symbol)
                    self._latest_tickers[symbol] = ticker
                except Exception as t_err:
                    logger.debug(f"[{key}] REST ticker fetch error: {t_err}")

                if raw_candles:
                    status.last_message_time = now_ms

                    # Populate base history if needed
                    if len(self._candle_histories.get(key, [])) < 30:
                        self._candle_histories[key] = list(raw_candles[:-1])

                    # Process preceding completed closed candle if timestamp changed
                    if len(raw_candles) >= 2:
                        prev_candle = raw_candles[-2]
                        if prev_candle.timestamp > last_closed_ts:
                            last_closed_ts = prev_candle.timestamp
                            await self._handle_candle_update(
                                prev_candle,
                                is_final_closed=True,
                                event_time=now_ms,
                                symbol=symbol,
                                timeframe=timeframe,
                                status=status,
                            )

                    # Process latest forming candle
                    latest_candle = raw_candles[-1]
                    await self._handle_candle_update(
                        latest_candle,
                        is_final_closed=False,
                        event_time=now_ms,
                        symbol=symbol,
                        timeframe=timeframe,
                        status=status,
                    )

                consecutive_errors = 0
                status.state = ConnectionStateEnum.LIVE
                status.message = "Connected (REST market data fallback active)"

                # 3. Periodically probe WebSocket to seamlessly return to WS when available
                if time.time() - last_ws_retry_time > ws_probe_interval:
                    last_ws_retry_time = time.time()
                    try:
                        probe_url = build_ws_stream_url(self.base_ws_url, symbol, timeframe)
                        async with websockets.connect(probe_url, close_timeout=3, open_timeout=5) as probe_ws:
                            logger.info(f"[Binance WS] Probe succeeded on {probe_url}. Resuming native WebSocket for {key}")
                            return  # Exit REST polling to allow native WebSocket connection
                    except Exception:
                        pass  # Continue in REST fallback mode

            except asyncio.CancelledError:
                break
            except Exception as ex:
                consecutive_errors += 1
                logger.warning(f"[{key}] REST fallback polling error ({consecutive_errors}): {ex}")
                if consecutive_errors > 5:
                    status.state = ConnectionStateEnum.RECONNECTING
                    status.message = f"REST polling degraded: {ex}"

            await asyncio.sleep(1.5)

    async def _stream_worker(self, symbol: str, timeframe: str):
        key = f"{symbol}@{timeframe}"
        ws_endpoint = build_ws_stream_url(self.base_ws_url, symbol, timeframe)

        status = MarketConnectionStatus(
            state=ConnectionStateEnum.RECONNECTING,
            symbol=symbol,
            timeframe=timeframe,
            last_ping=int(time.time() * 1000),
            last_message_time=0,
            reconnect_attempts=0,
            message=f"Connecting to Binance WebSocket...",
        )
        self._connection_states[key] = status
        self._candle_histories[key] = []

        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while self._running:
            try:
                status.reconnect_attempts += 1
                logger.info(f"[Binance WS] Connecting to {ws_endpoint} for {key} (attempt {status.reconnect_attempts})")

                async with websockets.connect(
                    ws_endpoint,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                    max_size=2**20,
                ) as ws:
                    status.state = ConnectionStateEnum.LIVE
                    status.reconnect_attempts = 0
                    status.message = "Connected and receiving live market stream"
                    reconnect_delay = 1.0
                    logger.info(f"[Binance WS] Connected: live stream active for {key}")

                    async for message in ws:
                        now_ms = int(time.time() * 1000)
                        status.last_message_time = now_ms
                        status.last_ping = now_ms

                        try:
                            raw_data = json.loads(message)
                        except json.JSONDecodeError as json_err:
                            logger.warning(f"[{key}] Received malformed JSON: {json_err}")
                            continue

                        event_data = raw_data.get("data", raw_data)
                        event_type = event_data.get("e")

                        if event_type == "kline":
                            k = event_data.get("k", {})
                            event_time = event_data.get("E", now_ms)
                            is_final_closed = bool(k.get("x", False))

                            last_event_time = self._last_event_times.get(key, 0)
                            if event_time < last_event_time:
                                continue
                            self._last_event_times[key] = event_time

                            try:
                                candle = Candle(
                                    timestamp=int(k["t"]),
                                    open=float(k["o"]),
                                    high=float(k["h"]),
                                    low=float(k["l"]),
                                    close=float(k["c"]),
                                    volume=float(k["v"]),
                                    close_time=int(k["T"]),
                                    quote_volume=float(k.get("q", 0)),
                                    trades_count=int(k.get("n", 0)),
                                    is_closed=is_final_closed,
                                    state=CandleStateEnum.CLOSED if is_final_closed else CandleStateEnum.UPDATING,
                                )
                                await self._handle_candle_update(
                                    candle=candle,
                                    is_final_closed=is_final_closed,
                                    event_time=event_time,
                                    symbol=symbol,
                                    timeframe=timeframe,
                                    status=status,
                                )
                            except Exception as parse_ex:
                                logger.error(f"[{key}] Error handling kline event: {parse_ex}", exc_info=True)

                        elif event_type == "24hrTicker":
                            try:
                                ticker = Ticker(
                                    symbol=event_data["s"],
                                    price=float(event_data["c"]),
                                    price_change=float(event_data["p"]),
                                    price_change_percent=float(event_data["P"]),
                                    high_24h=float(event_data["h"]),
                                    low_24h=float(event_data["l"]),
                                    volume_24h=float(event_data["v"]),
                                    quote_volume_24h=float(event_data["q"]),
                                    timestamp=int(event_data.get("E", now_ms)),
                                )
                                self._latest_tickers[symbol] = ticker
                            except Exception as ticker_ex:
                                logger.debug(f"Ticker parse error: {ticker_ex}")

            except Exception as conn_err:
                if isinstance(conn_err, asyncio.CancelledError):
                    status.state = ConnectionStateEnum.OFFLINE
                    status.message = "Stream task stopped"
                    logger.info(f"[{key}] Stream worker cancelled.")
                    break

                logger.warning(f"[Binance WS] Disconnected: {conn_err} for {key}")

                # Check if error is HTTP 451 or cloud geographic restriction
                if _is_http_451_error(conn_err):
                    logger.warning(
                        f"[Binance WS] Received HTTP 451 / geographic rejection for {key}. "
                        f"Activating public REST polling fallback..."
                    )
                    await self._rest_polling_fallback(symbol, timeframe, status)
                    continue

                status.state = ConnectionStateEnum.RECONNECTING
                status.message = f"Connection dropped ({conn_err}). Retrying in {reconnect_delay:.1f}s..."
                logger.info(f"[Binance WS] Reconnecting to {ws_endpoint} for {key} in {reconnect_delay:.1f}s")

            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

    async def start(self, default_symbol: str = "BTCUSDT", default_timeframe: str = "15m"):
        self._running = True
        self._ensure_stream_task(default_symbol, default_timeframe)
        logger.info(f"[Binance WS] Manager started for {default_symbol}@{default_timeframe}")

    async def stop(self):
        self._running = False
        for key, task in self._active_tasks.items():
            if not task.done():
                task.cancel()
        self._active_tasks.clear()
        for key in self._connection_states:
            self._connection_states[key].state = ConnectionStateEnum.OFFLINE
            self._connection_states[key].message = "Service stopped"
        logger.info("[Binance WS] ResilientBinanceWebSocketManager stopped cleanly.")


ws_manager = ResilientBinanceWebSocketManager()
