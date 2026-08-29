"""
SCALP_STRATEGY_V2 API Endpoints.
Provides:
  - GET /api/v1/scalp-v2 : Confirmed and preview V2 scalp signals
  - GET /api/v1/scalp-v2/stats : Frequency and setup diagnostic statistics
  - GET /api/v1/scalp-v2/history : In-memory recent signal history
  - GET /api/v1/scalp/compare : Side-by-side comparison of V1 vs V2
"""
import time
from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException

from app.data.base import MarketDataProvider
from app.data.binance import BinanceMarketDataProvider
from app.scalp.engine import ScalpStrategyEngine
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import (
    ScalpV2Response,
    ScalpV2StatsResponse,
    ScalpV2HistoryItem,
    ScalpCompareResponse,
)
from app.scalp_v2.evaluation import (
    ScalpV2EvaluationReport,
    run_scalp_v2_historical_evaluation,
)
from app.scalp_v2.diagnostics import (
    ScalpV2DiagnosticReport,
    ScalpV2DiagnosticEngine,
)

router = APIRouter()


def get_market_provider() -> MarketDataProvider:
    return BinanceMarketDataProvider()


@router.get(
    "",
    response_model=ScalpV2Response,
    summary="SCALP_STRATEGY_V2 — 1m higher-frequency scalp signal",
    description="Compute a higher-frequency 1m scalp signal recognizing Continuation, Pullback, and Breakout setups.",
)
async def get_scalp_v2_signal(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    include_preview: bool = Query(True, description="Include forming-candle preview"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()

    # ── Fetch 1m data ────────────────────────────────────────────────────────
    candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe="1m", limit=300)
    if not candles_1m:
        raise HTTPException(status_code=503, detail="No 1m candle data available")

    # ── Fetch 5m / 15m context ───────────────────────────────────────────────
    try:
        candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=100)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines(symbol=symbol, timeframe="15m", limit=60)
    except Exception:
        candles_15m = []

    # ── Confirmed V2 signal (closed candles only) ─────────────────────────────
    confirmed = ScalpV2StrategyEngine.evaluate(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
        is_preview=False,
    )

    # ── Preview V2 signal (including forming candle) ──────────────────────────
    preview = None
    if include_preview:
        try:
            preview = ScalpV2StrategyEngine.evaluate(
                candles_1m=candles_1m,
                candles_5m=candles_5m,
                candles_15m=candles_15m,
                symbol=symbol,
                is_preview=True,
            )
        except Exception:
            preview = None

    return ScalpV2Response(
        confirmed_signal=confirmed,
        preview_signal=preview,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get(
    "/stats",
    response_model=ScalpV2StatsResponse,
    summary="SCALP_STRATEGY_V2 — Signal frequency statistics",
    description="Internal diagnostic stats reporting signal frequency (1h, 4h, 24h) and setup distribution.",
)
async def get_scalp_v2_stats(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
):
    symbol = symbol.upper()
    return ScalpV2StrategyEngine.get_stats(symbol=symbol)


@router.get(
    "/history",
    response_model=List[ScalpV2HistoryItem],
    summary="SCALP_STRATEGY_V2 — Recent signal history",
    description="Returns recent confirmed V2 signals from in-memory history.",
)
async def get_scalp_v2_history(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    limit: int = Query(50, ge=1, le=100, description="Max history items"),
):
    symbol = symbol.upper()
    return ScalpV2StrategyEngine.get_history(symbol=symbol, limit=limit)


@router.get(
    "/evaluation",
    response_model=ScalpV2EvaluationReport,
    summary="SCALP_STRATEGY_V2 — Historical Signal Quality Evaluation",
    description="Evaluates V2 chronologically over historical 1m candles for horizon and score quality metrics.",
)
async def get_scalp_v2_evaluation(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    limit: int = Query(1000, ge=100, le=1000, description="1m candles to evaluate"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()
    candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe="1m", limit=limit)
    if not candles_1m:
        raise HTTPException(status_code=503, detail="No 1m candle data available for evaluation")

    try:
        candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=200)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines(symbol=symbol, timeframe="15m", limit=100)
    except Exception:
        candles_15m = []

    report = run_scalp_v2_historical_evaluation(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
    )
    return report


@router.get(
    "/diagnostics",
    response_model=ScalpV2DiagnosticReport,
    summary="SCALP_STRATEGY_V2 — Calibration & Timing Diagnostics",
    description="Deep diagnostic and calibration forensics layer for SCALP_STRATEGY_V2.",
)
async def get_scalp_v2_diagnostics(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    limit: int = Query(1000, ge=100, le=1000, description="1m candles to evaluate"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()
    candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe="1m", limit=limit)
    if not candles_1m:
        raise HTTPException(status_code=503, detail="No 1m candle data available for diagnostics")

    try:
        candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=200)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines(symbol=symbol, timeframe="15m", limit=100)
    except Exception:
        candles_15m = []

    report = ScalpV2DiagnosticEngine.run_diagnostics(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
    )
    return report


# Router for comparison endpoint
compare_router = APIRouter()


@compare_router.get(
    "/compare",
    response_model=ScalpCompareResponse,
    summary="SCALP Strategy Comparison — V1 vs V2 Side-by-Side",
    description="Evaluates V1 and V2 on identical candle inputs for objective research comparison.",
)
async def compare_scalp_strategies(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()

    candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe="1m", limit=300)
    if not candles_1m:
        raise HTTPException(status_code=503, detail="No 1m candle data available")

    try:
        candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=100)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines(symbol=symbol, timeframe="15m", limit=60)
    except Exception:
        candles_15m = []

    # Evaluate V1
    v1_sig = ScalpStrategyEngine.evaluate(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
        is_preview=False,
    )

    # Evaluate V2
    v2_sig = ScalpV2StrategyEngine.evaluate(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
        is_preview=False,
    )

    v2_stats = ScalpV2StrategyEngine.get_stats(symbol=symbol)

    return ScalpCompareResponse(
        symbol=symbol,
        timeframe="1m",
        calculation_timestamp=int(time.time() * 1000),
        v1={
            "strategy_id": v1_sig.strategy_id,
            "version": v1_sig.strategy_version,
            "direction": v1_sig.direction.value,
            "score": v1_sig.score_breakdown.normalised_score,
            "net_score": v1_sig.score_breakdown.net_score,
            "trade_plan": v1_sig.trade_plan.dict(),
            "reasons": v1_sig.reasons,
        },
        v2={
            "strategy_id": v2_sig.strategy_id,
            "version": v2_sig.strategy_version,
            "direction": v2_sig.direction.value,
            "trade_state": v2_sig.trade_state.value,
            "setup_type": v2_sig.setup_type.value,
            "score": v2_sig.score,
            "alignment_score": v2_sig.alignment_score,
            "strength": v2_sig.strength.value,
            "entry": v2_sig.entry.dict(),
            "stop_loss": v2_sig.stop_loss.dict(),
            "take_profits": v2_sig.take_profits.dict(),
            "supporting_factors": v2_sig.supporting_factors,
            "frequency_signals_last_24h": v2_stats.signals_last_24_hours,
        },
    )
