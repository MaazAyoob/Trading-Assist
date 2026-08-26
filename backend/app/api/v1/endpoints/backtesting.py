"""
FastAPI REST endpoints for the Phase 6 Backtesting & Validation Engine.
Provides backtest execution, run history, multi-dimensional metrics, and signal outcome records.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.data.binance import BinanceMarketDataProvider
from app.backtesting.config import BacktestConfig, CostModelConfig
from app.backtesting.engine import BacktestEngine
from app.backtesting.models import BacktestRun, BacktestMetrics, SignalOutcome
from app.models.backtest import BacktestRunModel, BacktestSignalOutcomeModel
from app.core.timeframes import SUPPORTED_TIMEFRAMES
from app.core.logging import logger

router = APIRouter()


class RunBacktestRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT")
    timeframe: str = Field(default="15m")
    candle_count: int = Field(default=300, ge=60, le=1000)
    horizons: List[int] = Field(default=[1, 3, 5, 10, 20])
    warmup_bars: int = Field(default=50, ge=30)
    fee_bps: float = Field(default=0.0, ge=0.0)
    slippage_bps: float = Field(default=0.0, ge=0.0)


@router.post("/run", response_model=BacktestRun)
async def execute_backtest(
    request: RunBacktestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a deterministic causal backtest over historical candles and persists the run and outcomes.
    """
    symbol = request.symbol.upper()
    timeframe = request.timeframe

    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timeframe '{timeframe}'. Supported: {SUPPORTED_TIMEFRAMES}",
        )

    provider = BinanceMarketDataProvider()
    try:
        candles = await provider.get_historical_klines(
            symbol=symbol,
            timeframe=timeframe,
            limit=request.candle_count,
        )
    except Exception as e:
        logger.error(f"Failed to fetch candles for backtest: {e}")
        raise HTTPException(status_code=502, detail=f"Exchange data retrieval failed: {str(e)}")

    if len(candles) < request.warmup_bars:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candles retrieved ({len(candles)}) for warmup ({request.warmup_bars}).",
        )

    cost_cfg = CostModelConfig(
        enabled=(request.fee_bps > 0 or request.slippage_bps > 0),
        fee_bps=request.fee_bps,
        slippage_bps=request.slippage_bps,
    )

    config = BacktestConfig(
        symbol=symbol,
        timeframe=timeframe,
        warmup_bars=request.warmup_bars,
        horizons=request.horizons,
        cost_model=cost_cfg,
    )

    # Pure causal sequential execution
    run = BacktestEngine.run(candles=candles, config=config)

    # Persist run in isolated DB tables
    try:
        run_record = BacktestRunModel(
            run_id=run.run_id,
            symbol=run.symbol,
            timeframe=run.timeframe,
            start_timestamp=run.start_timestamp,
            end_timestamp=run.end_timestamp,
            candle_count=run.dataset_metadata.candle_count,
            signal_count=len(run.signal_outcomes),
            dataset_hash=run.dataset_metadata.sha256_hash,
            backtest_engine_version=run.config.backtest_engine_version,
            backtest_config_version=run.config.backtest_config_version,
            signal_engine_version="0.5.0",
            config_json=run.config.model_dump(),
            metrics_json=run.metrics.model_dump(),
            integrity_json=run.integrity_report.model_dump(),
            dataset_metadata_json=run.dataset_metadata.model_dump(),
            status=run.status,
            created_timestamp=run.created_timestamp,
        )
        db.add(run_record)

        for s in run.signal_outcomes:
            outcomes_dict = {str(k): v.model_dump() for k, v in s.outcomes.items()}
            sig_record = BacktestSignalOutcomeModel(
                run_id=run.run_id,
                signal_id=s.signal_id,
                symbol=s.symbol,
                timeframe=s.timeframe,
                signal_timestamp=s.signal_timestamp,
                signal_direction=s.signal_direction,
                signal_strength=s.signal_strength,
                signal_score=s.signal_score,
                entry_reference_price=s.entry_reference_price,
                outcomes_json=outcomes_dict,
                regime_at_signal=s.regime_at_signal,
                structure_at_signal=s.structure_at_signal,
                volatility_at_signal=s.volatility_at_signal,
            )
            db.add(sig_record)

        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist backtest run to database: {e}")
        await db.rollback()

    return run


@router.get("/runs")
async def list_backtest_runs(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists previously executed historical backtest runs.
    """
    stmt = select(BacktestRunModel).order_by(desc(BacktestRunModel.created_timestamp)).limit(limit)
    if symbol:
        stmt = stmt.where(BacktestRunModel.symbol == symbol.upper())
    if timeframe:
        stmt = stmt.where(BacktestRunModel.timeframe == timeframe)

    result = await db.execute(stmt)
    runs = result.scalars().all()

    return [
        {
            "run_id": r.run_id,
            "symbol": r.symbol,
            "timeframe": r.timeframe,
            "start_timestamp": r.start_timestamp,
            "end_timestamp": r.end_timestamp,
            "candle_count": r.candle_count,
            "signal_count": r.signal_count,
            "dataset_hash": r.dataset_hash,
            "status": r.status,
            "created_timestamp": r.created_timestamp,
            "metrics_summary": {
                "signals_per_day": r.metrics_json.get("signals_per_day", 0.0),
                "long_signals": r.metrics_json.get("long_signals", 0),
                "short_signals": r.metrics_json.get("short_signals", 0),
            },
        }
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=BacktestRun)
async def get_backtest_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full details, configuration, and multi-dimensional metrics for a specific backtest run.
    """
    stmt = select(BacktestRunModel).where(BacktestRunModel.run_id == run_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")

    # Fetch outcomes
    outcomes_stmt = select(BacktestSignalOutcomeModel).where(BacktestSignalOutcomeModel.run_id == run_id)
    outcomes_res = await db.execute(outcomes_stmt)
    outcome_records = outcomes_res.scalars().all()

    outcomes_list = []
    for o in outcome_records:
        parsed_outcomes = {int(k): v for k, v in o.outcomes_json.items()}
        outcomes_list.append(
            SignalOutcome(
                signal_id=o.signal_id,
                symbol=o.symbol,
                timeframe=o.timeframe,
                signal_timestamp=o.signal_timestamp,
                signal_direction=o.signal_direction,
                signal_strength=o.signal_strength,
                signal_score=o.signal_score,
                entry_reference_price=o.entry_reference_price,
                outcomes=parsed_outcomes,
                regime_at_signal=o.regime_at_signal,
                structure_at_signal=o.structure_at_signal,
                volatility_at_signal=o.volatility_at_signal,
                engine_version=record.signal_engine_version,
                config_version=record.backtest_config_version,
            )
        )

    return BacktestRun(
        run_id=record.run_id,
        symbol=record.symbol,
        timeframe=record.timeframe,
        start_timestamp=record.start_timestamp,
        end_timestamp=record.end_timestamp,
        dataset_metadata=record.dataset_metadata_json,
        config=record.config_json,
        metrics=record.metrics_json,
        signal_outcomes=outcomes_list,
        integrity_report=record.integrity_json,
        status=record.status,
        created_timestamp=record.created_timestamp,
    )


@router.get("/runs/{run_id}/metrics", response_model=BacktestMetrics)
async def get_backtest_metrics(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the comprehensive metrics dictionary and conditional performance breakdowns.
    """
    stmt = select(BacktestRunModel).where(BacktestRunModel.run_id == run_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")

    return BacktestMetrics(**record.metrics_json)


@router.get("/runs/{run_id}/signals", response_model=List[SignalOutcome])
async def get_backtest_signals(
    run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns individual signal outcome records for a specific backtest run.
    """
    stmt = (
        select(BacktestSignalOutcomeModel)
        .where(BacktestSignalOutcomeModel.run_id == run_id)
        .order_by(BacktestSignalOutcomeModel.signal_timestamp)
        .limit(limit)
    )
    result = await db.execute(stmt)
    outcome_records = result.scalars().all()

    outcomes_list = []
    for o in outcome_records:
        parsed_outcomes = {int(k): v for k, v in o.outcomes_json.items()}
        outcomes_list.append(
            SignalOutcome(
                signal_id=o.signal_id,
                symbol=o.symbol,
                timeframe=o.timeframe,
                signal_timestamp=o.signal_timestamp,
                signal_direction=o.signal_direction,
                signal_strength=o.signal_strength,
                signal_score=o.signal_score,
                entry_reference_price=o.entry_reference_price,
                outcomes=parsed_outcomes,
                regime_at_signal=o.regime_at_signal,
                structure_at_signal=o.structure_at_signal,
                volatility_at_signal=o.volatility_at_signal,
                engine_version="0.5.0",
                config_version="2026-08-24-v1",
            )
        )

    return outcomes_list
