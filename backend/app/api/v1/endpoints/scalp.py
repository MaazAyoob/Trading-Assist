"""
SCALP_STRATEGY_V1 API endpoint.

GET /api/v1/scalp  — compute a scalp signal for the given symbol on 1m.

This endpoint is SEPARATE from Phase 5, Phase 10, or any other engine.
It does NOT call SignalEngine or TradeDecisionEngine as a gate.
"""
import time
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

from app.data.base import MarketDataProvider
from app.data.binance import BinanceMarketDataProvider
from app.scalp.engine import ScalpStrategyEngine
from app.scalp.models import ScalpSignal

router = APIRouter()


def get_market_provider() -> MarketDataProvider:
    return BinanceMarketDataProvider()


class ScalpResponse(BaseModel):
    confirmed_signal: ScalpSignal
    preview_signal: Optional[ScalpSignal] = None
    calculation_timestamp: int


@router.get(
    "",
    response_model=ScalpResponse,
    summary="SCALP_STRATEGY_V1 — 1m scalp signal",
    description=(
        "Compute a deterministic scalp signal for the given symbol on 1m candles. "
        "Independent of Phase 5 and Phase 10. "
        "Phase 5 direction is included as read-only context only."
    ),
)
async def get_scalp_signal(
    symbol: str = Query("BTCUSDT", description="Trading pair"),
    include_preview: bool = Query(True, description="Include forming-candle preview"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    symbol = symbol.upper()

    # ── Fetch 1m data ────────────────────────────────────────────────────────
    candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe="1m", limit=300)
    if not candles_1m:
        raise HTTPException(status_code=503, detail="No 1m candle data available")

    # ── Fetch 5m / 15m context (optional — don't fail if unavailable) ────────
    try:
        candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=100)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines(symbol=symbol, timeframe="15m", limit=60)
    except Exception:
        candles_15m = []

    # ── Read Phase 5 direction as display context (NOT a gate) ───────────────
    phase5_direction = "NEUTRAL"
    try:
        from app.signals.engine import MultiFactorSignalEngine
        closed_1m = [c for c in candles_1m if c.is_closed]
        if len(closed_1m) >= 60:
            p5_signal = MultiFactorSignalEngine.compute_signal(
                closed_1m, symbol=symbol, timeframe="1m"
            )
            phase5_direction = p5_signal.direction.value if p5_signal else "NEUTRAL"
    except Exception:
        phase5_direction = "NEUTRAL"

    # ── Confirmed scalp signal (closed candles only) ─────────────────────────
    confirmed = ScalpStrategyEngine.evaluate(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol=symbol,
        phase5_direction=phase5_direction,
        is_preview=False,
    )

    # ── Preview scalp signal (including forming candle) ──────────────────────
    preview: Optional[ScalpSignal] = None
    if include_preview:
        try:
            preview = ScalpStrategyEngine.evaluate(
                candles_1m=candles_1m,
                candles_5m=candles_5m,
                candles_15m=candles_15m,
                symbol=symbol,
                phase5_direction=phase5_direction,
                is_preview=True,
            )
        except Exception:
            preview = None

    return ScalpResponse(
        confirmed_signal=confirmed,
        preview_signal=preview,
        calculation_timestamp=int(time.time() * 1000),
    )
