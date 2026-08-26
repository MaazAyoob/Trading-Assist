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
from app.indicators.base import IndicatorSnapshot, IndicatorHistoryPoint
from app.indicators.engine import IndicatorEngine
from app.regime.models import MarketRegimeSnapshot
from app.regime.engine import MarketRegimeEngine
from app.structure.models import MarketStructureSnapshot, StructureEvent, SwingPoint, SupportResistanceZone
from app.structure.engine import MarketStructureEngine
from app.signals.models import ResearchSignal
from app.signals.engine import MultiFactorSignalEngine

router = APIRouter()


def get_market_provider() -> MarketDataProvider:
    return BinanceMarketDataProvider()


class AnalysisIndicatorsResponse(BaseModel):
    symbol: str
    timeframe: str
    quality: MarketDataQuality
    latest_candle: Optional[Candle] = None
    confirmed_snapshot: IndicatorSnapshot
    realtime_snapshot: Optional[IndicatorSnapshot] = None
    calculation_timestamp: int


class AnalysisRegimeResponse(BaseModel):
    symbol: str
    timeframe: str
    quality: MarketDataQuality
    confirmed_snapshot: MarketRegimeSnapshot
    realtime_snapshot: Optional[MarketRegimeSnapshot] = None
    calculation_timestamp: int


class AnalysisStructureResponse(BaseModel):
    symbol: str
    timeframe: str
    quality: MarketDataQuality
    confirmed_snapshot: MarketStructureSnapshot
    realtime_snapshot: Optional[MarketStructureSnapshot] = None
    calculation_timestamp: int


class AnalysisSignalResponse(BaseModel):
    symbol: str
    timeframe: str
    quality: MarketDataQuality
    confirmed_signal: ResearchSignal
    realtime_signal: Optional[ResearchSignal] = None
    calculation_timestamp: int


@router.get("/indicators", response_model=AnalysisIndicatorsResponse, summary="Get calculated technical indicators")
async def get_indicators(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="Trading pair symbol (e.g. BTCUSDT)"),
    timeframe: str = Query(default="15m", description="Candle interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(default=300, ge=50, le=1000, description="Historical lookback candle count"),
    include_realtime: bool = Query(default=False, description="Whether to include unconfirmed forming-candle calculations"),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)

    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    confirmed_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles,
        symbol=symbol,
        timeframe=timeframe,
        is_confirmed=True,
        quality_status=quality.status,
    )

    realtime_snapshot = None
    if include_realtime and clean_candles:
        realtime_snapshot = IndicatorEngine.calculate_snapshot(
            clean_candles,
            symbol=symbol,
            timeframe=timeframe,
            is_confirmed=False,
            quality_status=quality.status,
        )

    latest_candle = clean_candles[-1] if clean_candles else None

    return AnalysisIndicatorsResponse(
        symbol=symbol,
        timeframe=timeframe,
        quality=quality,
        latest_candle=latest_candle,
        confirmed_snapshot=confirmed_snapshot,
        realtime_snapshot=realtime_snapshot,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get("/indicators/history", response_model=List[IndicatorHistoryPoint], summary="Get historical indicator series for charts")
async def get_indicator_history(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=200, ge=10, le=500),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=min(limit + 100, 1000))
    clean_candles, _ = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    history = IndicatorEngine.calculate_history(clean_candles, symbol=symbol, timeframe=timeframe, limit=limit)
    return history


@router.get("/regime", response_model=AnalysisRegimeResponse, summary="Get current market regime classification")
async def get_regime(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=300, ge=50, le=1000),
    include_realtime: bool = Query(default=False),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    ind_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status
    )
    struct_snapshot = MarketStructureEngine.evaluate(
        clean_candles, indicators=ind_snapshot, is_confirmed=True
    )
    confirmed_regime = MarketRegimeEngine.classify(
        candles=clean_candles,
        indicators=ind_snapshot,
        structure_state=struct_snapshot.structure_direction,
        is_confirmed=True,
    )

    realtime_regime = None
    if include_realtime and clean_candles:
        realtime_ind = IndicatorEngine.calculate_snapshot(
            clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=False, quality_status=quality.status
        )
        realtime_regime = MarketRegimeEngine.classify(
            candles=clean_candles,
            indicators=realtime_ind,
            structure_state=struct_snapshot.structure_direction,
            is_confirmed=False,
        )

    return AnalysisRegimeResponse(
        symbol=symbol,
        timeframe=timeframe,
        quality=quality,
        confirmed_snapshot=confirmed_regime,
        realtime_snapshot=realtime_regime,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get("/regime/history", response_model=List[MarketRegimeSnapshot], summary="Get historical regime snapshots")
async def get_regime_history(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=50, ge=10, le=200),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=min(limit + 150, 1000))
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    history: List[MarketRegimeSnapshot] = []
    step_candles = clean_candles[-limit:]
    for idx, c in enumerate(step_candles):
        sub_end = len(clean_candles) - limit + idx + 1
        sub_candles = clean_candles[:sub_end]
        if len(sub_candles) < 30:
            continue
        ind = IndicatorEngine.calculate_snapshot(sub_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status)
        struct = MarketStructureEngine.evaluate(sub_candles, indicators=ind, is_confirmed=True)
        regime = MarketRegimeEngine.classify(candles=sub_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
        history.append(regime)

    return history


@router.get("/structure", response_model=AnalysisStructureResponse, summary="Get market price structure analysis")
async def get_structure(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=300, ge=50, le=1000),
    include_realtime: bool = Query(default=False),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    ind_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status
    )
    confirmed_structure = MarketStructureEngine.evaluate(
        clean_candles, indicators=ind_snapshot, is_confirmed=True
    )

    realtime_structure = None
    if include_realtime and clean_candles:
        realtime_structure = MarketStructureEngine.evaluate(
            clean_candles, indicators=ind_snapshot, is_confirmed=False
        )

    return AnalysisStructureResponse(
        symbol=symbol,
        timeframe=timeframe,
        quality=quality,
        confirmed_snapshot=confirmed_structure,
        realtime_snapshot=realtime_structure,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get("/structure/history", response_model=MarketStructureSnapshot, summary="Get confirmed structure events and zones")
async def get_structure_history(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
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

    ind_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status
    )
    return MarketStructureEngine.evaluate(clean_candles, indicators=ind_snapshot, is_confirmed=True)


@router.get("/signal", response_model=AnalysisSignalResponse, summary="Get current Multi-Factor Research Signal")
async def get_signal(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=300, ge=50, le=1000),
    include_realtime: bool = Query(default=False),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    # 1. Indicators
    ind_snapshot = IndicatorEngine.calculate_snapshot(
        clean_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status
    )
    # 2. Structure
    struct_snapshot = MarketStructureEngine.evaluate(
        clean_candles, indicators=ind_snapshot, is_confirmed=True
    )
    # 3. Regime
    regime_snapshot = MarketRegimeEngine.classify(
        candles=clean_candles,
        indicators=ind_snapshot,
        structure_state=struct_snapshot.structure_direction,
        is_confirmed=True,
    )
    # 4. Multi-Factor Research Signal
    confirmed_signal = MultiFactorSignalEngine.calculate_signal(
        candles=clean_candles,
        indicators=ind_snapshot,
        regime=regime_snapshot,
        structure=struct_snapshot,
        quality=quality,
        is_confirmed=True,
    )

    realtime_signal = None
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

    return AnalysisSignalResponse(
        symbol=symbol,
        timeframe=timeframe,
        quality=quality,
        confirmed_signal=confirmed_signal,
        realtime_signal=realtime_signal,
        calculation_timestamp=int(time.time() * 1000),
    )


@router.get("/signal/history", response_model=List[ResearchSignal], summary="Get historical confirmed research signals")
async def get_signal_history(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=50, ge=10, le=200),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=min(limit + 150, 1000))
    clean_candles, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )

    history: List[ResearchSignal] = []
    step_candles = clean_candles[-limit:]
    for idx, c in enumerate(step_candles):
        sub_end = len(clean_candles) - limit + idx + 1
        sub_candles = clean_candles[:sub_end]
        if len(sub_candles) < 35:
            continue
        ind = IndicatorEngine.calculate_snapshot(sub_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status)
        struct = MarketStructureEngine.evaluate(sub_candles, indicators=ind, is_confirmed=True)
        regime = MarketRegimeEngine.classify(candles=sub_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
        signal = MultiFactorSignalEngine.calculate_signal(
            candles=sub_candles,
            indicators=ind,
            regime=regime,
            structure=struct,
            quality=quality,
            is_confirmed=True,
        )
        history.append(signal)

    return history


@router.get("/signal/explain", response_model=ResearchSignal, summary="Get full calculation trace and evidence breakdown for a signal")
async def explain_signal(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    timestamp: Optional[int] = Query(default=None, description="Candle timestamp to explain (defaults to latest)"),
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
            raise HTTPException(status_code=404, detail=f"Candle with timestamp {timestamp} not found in available lookback window")
        target_candles = clean_candles[: idx_match[0] + 1]

    ind = IndicatorEngine.calculate_snapshot(target_candles, symbol=symbol, timeframe=timeframe, is_confirmed=True, quality_status=quality.status)
    struct = MarketStructureEngine.evaluate(target_candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=target_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    return MultiFactorSignalEngine.calculate_signal(
        candles=target_candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        quality=quality,
        is_confirmed=True,
    )


@router.get("/quality", response_model=MarketDataQuality, summary="Get market data quality evaluation")
async def get_data_quality(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=200, ge=10, le=1000),
    provider: MarketDataProvider = Depends(get_market_provider),
):
    if timeframe not in settings.SUPPORTED_TIMEFRAMES:
        raise TimeframeNotSupportedException(timeframe)

    symbol = symbol.upper()
    raw_candles = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=limit)
    _, quality = MarketDataQualityValidator.validate_dataset(
        raw_candles, symbol=symbol, timeframe=timeframe, min_required=1
    )
    return quality
