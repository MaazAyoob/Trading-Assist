"""
Phase 10 — Trade Decision REST API Endpoints.
Provides deterministic, strictly analytical trade plans, multi-candidate comparisons,
and audit trails. No order placement or trading APIs exist.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.errors import TimeframeNotSupportedException
from app.data.base import MarketDataProvider
from app.data.binance import BinanceMarketDataProvider
from app.data.quality import MarketDataQualityValidator
from app.data.schema import Candle, MarketDataQuality
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.models import TradePlan, MultiStrategyTradeDecisions
from app.trade_decision.engine import TradeDecisionEngine

router = APIRouter()


def get_market_provider() -> MarketDataProvider:
    return BinanceMarketDataProvider()


class AnalysisTradeDecisionResponse(BaseModel):
    symbol: str
    timeframe: str
    quality: MarketDataQuality
    confirmed_decision: TradePlan
    realtime_preview: Optional[TradePlan] = None
    multi_strategy: MultiStrategyTradeDecisions
    calculation_timestamp: int


@router.get("", response_model=AnalysisTradeDecisionResponse, summary="Get current deterministic trade decision & risk plan")
async def get_trade_decision(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol (e.g. BTCUSDT)"),
    timeframe: str = Query(default="15m", description="Candle interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    strategy_context_id: str = Query(default="EXP_A2_PULLBACK_VWAP", description="Strategy context ID (EXP_A2_PULLBACK_VWAP, EXP_E2_EXTENSION_VWAP, PHASE5_BASELINE)"),
    include_realtime: bool = Query(default=False, description="Whether to include unconfirmed forming candle preview"),
    limit: int = Query(default=300, ge=50, le=1000),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    # 1. Closed candle confirmed calculation pipeline
    ind_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status
    )
    struct_snapshot = MarketStructureEngine.evaluate(
        clean_candles, indicators=ind_snapshot, is_confirmed=True
    )
    regime_snapshot = MarketRegimeEngine.classify(
        candles=clean_candles,
        indicators=ind_snapshot,
        structure_state=struct_snapshot.structure_direction,
        is_confirmed=True,
    )
    confirmed_signal = MultiFactorSignalEngine.calculate_signal(
        candles=clean_candles,
        indicators=ind_snapshot,
        regime=regime_snapshot,
        structure=struct_snapshot,
        quality=quality,
        is_confirmed=True,
    )

    confirmed_decision = TradeDecisionEngine.calculate_decision(
        candles=clean_candles,
        indicators=ind_snapshot,
        regime=regime_snapshot,
        structure=struct_snapshot,
        signal=confirmed_signal,
        quality=quality,
        strategy_context_id=strategy_context_id,
        is_confirmed=True,
    )

    multi_strat = TradeDecisionEngine.calculate_multi_strategy_decisions(
        candles=clean_candles,
        indicators=ind_snapshot,
        regime=regime_snapshot,
        structure=struct_snapshot,
        signal=confirmed_signal,
        quality=quality,
        primary_strategy_id=strategy_context_id,
        is_confirmed=True,
    )

    # 2. Optional Realtime Forming Candle Preview
    realtime_preview = None
    if include_realtime and clean_candles:
        realtime_ind = IndicatorEngine.calculate_snapshot(
            clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=False, quality_status=quality.status
        )
        realtime_struct = MarketStructureEngine.evaluate(
            clean_candles, indicators=realtime_ind, is_confirmed=False
        )
        realtime_regime = MarketRegimeEngine.classify(
            candles=clean_candles,
            indicators=realtime_ind,
            structure_state=realtime_struct.structure_direction,
            is_confirmed=False,
        )
        realtime_signal = MultiFactorSignalEngine.calculate_signal(
            candles=clean_candles,
            indicators=realtime_ind,
            regime=realtime_regime,
            structure=realtime_struct,
            quality=quality,
            is_confirmed=False,
        )
        realtime_preview = TradeDecisionEngine.calculate_decision(
            candles=clean_candles,
            indicators=realtime_ind,
            regime=realtime_regime,
            structure=realtime_struct,
            signal=realtime_signal,
            quality=quality,
            strategy_context_id=strategy_context_id,
            is_confirmed=False,
        )

    return AnalysisTradeDecisionResponse(
        symbol=symbol,
        timeframe=timeframe,
        quality=quality,
        confirmed_decision=confirmed_decision,
        realtime_preview=realtime_preview,
        multi_strategy=multi_strat,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get("/history", response_model=List[TradePlan], summary="Get historical confirmed trade decision plans")
async def get_trade_decision_history(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    strategy_context_id: str = Query(default="EXP_A2_PULLBACK_VWAP"),
    limit: int = Query(default=50, ge=5, le=200),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=min(limit + 150, 1000))
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    history: List[TradePlan] = []
    step_candles = clean_candles[-limit:]
    for idx, c in enumerate(step_candles):
        sub_end = len(clean_candles) - limit + idx + 1
        sub_candles = clean_candles[:sub_end]
        if len(sub_candles) < 35:
            continue
        ind = IndicatorEngine.calculate_snapshot(sub_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status)
        struct = MarketStructureEngine.evaluate(sub_candles, indicators=ind, is_confirmed=True)
        regime = MarketRegimeEngine.classify(candles=sub_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
        sig = MultiFactorSignalEngine.calculate_signal(
            candles=sub_candles,
            indicators=ind,
            regime=regime,
            structure=struct,
            quality=quality,
            is_confirmed=True,
        )
        plan = TradeDecisionEngine.calculate_decision(
            candles=sub_candles,
            indicators=ind,
            regime=regime,
            structure=struct,
            signal=sig,
            quality=quality,
            strategy_context_id=strategy_context_id,
            is_confirmed=True,
        )
        history.append(plan)

    return history


@router.get("/explain", response_model=TradePlan, summary="Get full audit trail and explanation for a trade decision")
async def explain_trade_decision(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    strategy_context_id: str = Query(default="EXP_A2_PULLBACK_VWAP"),
    timestamp: Optional[int] = Query(default=None, description="Candle timestamp to explain (defaults to latest closed candle)"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=300)
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    target_candles = clean_candles
    if timestamp is not None:
        idx_match = [i for i, c in enumerate(clean_candles) if c.timestamp == timestamp]
        if not idx_match:
            raise HTTPException(status_code=404, detail=f"Candle with timestamp {timestamp} not found in lookback window")
        target_candles = clean_candles[: idx_match[0] + 1]

    ind = IndicatorEngine.calculate_snapshot(target_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status)
    struct = MarketStructureEngine.evaluate(target_candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=target_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    sig = MultiFactorSignalEngine.calculate_signal(
        candles=target_candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        quality=quality,
        is_confirmed=True,
    )
    return TradeDecisionEngine.calculate_decision(
        candles=target_candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=sig,
        quality=quality,
        strategy_context_id=strategy_context_id,
        is_confirmed=True,
    )
