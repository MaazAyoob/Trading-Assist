"""
API Endpoints for Phase 12 Trading Profiles & Multi-Horizon Orchestration.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.profiles.registry import profile_registry
from app.profiles.engine import TradingProfileEngine
from app.profile_validation.comparison import ProfileComparisonEngine
from app.profile_validation.evaluation import ProfileEvaluationRunner
from app.profile_validation.dataset import build_synthetic_multi_tf_dataset
from app.data.binance import BinanceMarketDataProvider
from app.profiles.models import (
    TradingProfileConfig,
    ProfileAnalysisResult,
    ProfileComparisonReport,
)

router = APIRouter()


@router.get("", response_model=List[TradingProfileConfig])
async def list_trading_profiles():
    """List all registered trading profiles with static parameters and configuration hashes."""
    return profile_registry.list_profiles()


@router.get("/compare", response_model=ProfileComparisonReport)
async def compare_profiles(
    symbol: str = Query(default="BTCUSDT", description="Target trading pair symbol"),
):
    """Generate side-by-side comparative matrix across all 5 profiles."""
    return ProfileComparisonEngine.generate_comparison_report(symbol=symbol)


@router.get("/{profile_id}", response_model=TradingProfileConfig)
async def get_trading_profile(profile_id: str):
    """Get single trading profile definition by profile_id."""
    profile = profile_registry.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Trading profile '{profile_id}' not found.")
    return profile


@router.get("/{profile_id}/context", response_model=ProfileAnalysisResult)
async def get_profile_context(
    profile_id: str,
    symbol: str = Query(default="BTCUSDT", description="Target symbol"),
    strategy_id: str = Query(default="EXP_A2_PULLBACK_VWAP", description="Candidate strategy context ID"),
):
    """
    Evaluates real-time / confirmed multi-timeframe analytical context for the chosen profile.
    Orchestrates primary and context timeframes causally.
    """
    profile = profile_registry.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Trading profile '{profile_id}' not found.")

    provider = BinanceMarketDataProvider()
    try:
        # Fetch primary candles
        primary_candles = await provider.get_historical_klines(symbol, profile.primary_timeframe, limit=200)
        
        # Fetch context candles for each context timeframe
        context_map = {}
        for ctx_tf in profile.context_timeframes:
            try:
                ctx_candles = await provider.get_historical_klines(symbol, ctx_tf, limit=100)
                context_map[ctx_tf] = ctx_candles
            except Exception:
                context_map[ctx_tf] = []

        result = TradingProfileEngine.evaluate_profile(
            symbol=symbol,
            profile_config=profile,
            primary_candles=primary_candles,
            context_candles_map=context_map,
            is_confirmed=True,
            strategy_context_id=strategy_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile evaluation error: {str(e)}")


@router.get("/{profile_id}/metrics")
async def get_profile_metrics(
    profile_id: str,
    symbol: str = Query(default="BTCUSDT", description="Target symbol"),
):
    """Evaluates forward returns, signal density, and cost sensitivity for the profile."""
    profile = profile_registry.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Trading profile '{profile_id}' not found.")

    dataset = build_synthetic_multi_tf_dataset(primary_count=250)
    return ProfileEvaluationRunner.evaluate_profile_over_dataset(
        symbol=symbol,
        profile_config=profile,
        multi_tf_dataset=dataset,
        warmup_bars=50,
    )
