"""
Predefined, immutable trading profile configurations for Phase 12.
All values are statically declared without runtime parameter mutations.
"""

from typing import Dict
from app.profiles.models import (
    ProfileEnum,
    ProfileLifecycleStatus,
    TradingProfileConfig,
)
from app.profiles.version import (
    PROFILE_SCALP_1M,
    PROFILE_INTRADAY_5M,
    PROFILE_TRADING_15M,
    PROFILE_SWING_4H,
    PROFILE_POSITION_1D,
    compute_profile_config_hash,
)

# ----------------------------------------------------
# 1. SCALP PROFILE (1m primary, 5m/15m context)
# ----------------------------------------------------
_scalp_dict = {
    "profile_id": PROFILE_SCALP_1M,
    "display_name": "⚡ SCALP",
    "description": "Short-duration analytical opportunity detection on 1m bars with 5m/15m causal context.",
    "profile_type": ProfileEnum.SCALP,
    "primary_timeframe": "1m",
    "context_timeframes": ["5m", "15m"],
    "expected_holding_horizon": "1–15 minutes (1–15 bars)",
    "minimum_data_requirements": 60,
    "volatility_policy": "ATR expansion filter; rejects extreme chop or low liquidity.",
    "structure_requirement": "1m micro-swings with 5m directional alignment; VWAP anchor interaction.",
    "signal_evaluation_behavior": "Short-term momentum & micro pullback confirmation without requiring multi-hour state lock.",
    "entry_planning_context": "PULLBACK_ZONE and VWAP equilibrium reference; strict R:R >= 1.20R.",
    "research_validation_requirements": "Strict transaction cost evaluation (0, 5, 10, 15 bps); high frequency without quality collapse.",
    "cost_sensitivity_bps": [0, 5, 10, 15],
    "status": ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE,
}
SCALP_1M_CONFIG = TradingProfileConfig(
    **_scalp_dict,
    config_hash=compute_profile_config_hash(_scalp_dict),
)

# ----------------------------------------------------
# 2. INTRADAY PROFILE (5m primary, 15m/1h context)
# ----------------------------------------------------
_intraday_dict = {
    "profile_id": PROFILE_INTRADAY_5M,
    "display_name": "📊 INTRADAY",
    "description": "Day-trading analytical setups on 5m bars with 15m directional context and 1h macro regime.",
    "profile_type": ProfileEnum.INTRADAY,
    "primary_timeframe": "5m",
    "context_timeframes": ["15m", "1h"],
    "expected_holding_horizon": "15–120 minutes (3–24 bars)",
    "minimum_data_requirements": 60,
    "volatility_policy": "Standard ATR and Bollinger width filtering.",
    "structure_requirement": "5m confirmed swing high/low breaks (BOS) aligned with 15m market structure.",
    "signal_evaluation_behavior": "Multi-factor confluence across trend, momentum, and volume expansion.",
    "entry_planning_context": "Pullback to EMA/VWAP zone with structural invalidation below 5m swing anchor.",
    "research_validation_requirements": "Standard cost tiers (0, 5, 10 bps); balanced intraday signal density.",
    "cost_sensitivity_bps": [0, 5, 10],
    "status": ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE,
}
INTRADAY_5M_CONFIG = TradingProfileConfig(
    **_intraday_dict,
    config_hash=compute_profile_config_hash(_intraday_dict),
)

# ----------------------------------------------------
# 3. TRADING PROFILE (15m primary, 1h/4h context)
# ----------------------------------------------------
_trading_dict = {
    "profile_id": PROFILE_TRADING_15M,
    "display_name": "🎯 TRADING",
    "description": "Medium-term intraday to multi-hour trading analysis matching the Phase 5/8 baseline environment.",
    "profile_type": ProfileEnum.TRADING,
    "primary_timeframe": "15m",
    "context_timeframes": ["1h", "4h"],
    "expected_holding_horizon": "1–8 hours (4–32 bars)",
    "minimum_data_requirements": 60,
    "volatility_policy": "Full Phase 4 regime volatility classification (Normal, Expanding, Compressing).",
    "structure_requirement": "Confirmed 15m swings with 3-bar causal delay and validated S&R support/resistance zones.",
    "signal_evaluation_behavior": "Authoritative Phase 5 Multi-Factor Signal Engine (v0.5.0) and Phase 8 candidate filters.",
    "entry_planning_context": "Phase 10 Trade Decision Engine with canonical targets (1.25R, 2.0R, 3.0R).",
    "research_validation_requirements": "Full Phase 6/9 backtesting & shadow validation compliance.",
    "cost_sensitivity_bps": [0, 5, 10],
    "status": ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE,
}
TRADING_15M_CONFIG = TradingProfileConfig(
    **_trading_dict,
    config_hash=compute_profile_config_hash(_trading_dict),
)

# ----------------------------------------------------
# 4. SWING PROFILE (4h primary, 1h/1d context)
# ----------------------------------------------------
_swing_dict = {
    "profile_id": PROFILE_SWING_4H,
    "display_name": "🌊 SWING",
    "description": "Multi-day swing analysis emphasizing macro structure, major S&R, and trend persistence.",
    "profile_type": ProfileEnum.SWING,
    "primary_timeframe": "4h",
    "context_timeframes": ["1h", "1d"],
    "expected_holding_horizon": "1–5 days (6–30 bars)",
    "minimum_data_requirements": 60,
    "volatility_policy": "Macro regime filtering; immune to micro intra-candle noise.",
    "structure_requirement": "Major 4h/1d swing structural pivots and institutional supply/demand clusters.",
    "signal_evaluation_behavior": "Persistent regime and trend confirmation across higher timeframes.",
    "entry_planning_context": "Structural pullback entries with wider ATR buffers (0.50–0.75 ATR) and macro targets.",
    "research_validation_requirements": "Multi-day holding return horizons and drawdown tolerance.",
    "cost_sensitivity_bps": [0, 5, 10],
    "status": ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE,
}
SWING_4H_CONFIG = TradingProfileConfig(
    **_swing_dict,
    config_hash=compute_profile_config_hash(_swing_dict),
)

# ----------------------------------------------------
# 5. POSITION PROFILE (1d primary, 4h/1w context)
# ----------------------------------------------------
_position_dict = {
    "profile_id": PROFILE_POSITION_1D,
    "display_name": "🏔️ POSITION",
    "description": "Longer-term analytical positioning based on daily/weekly macro trends and market cycles.",
    "profile_type": ProfileEnum.POSITION,
    "primary_timeframe": "1d",
    "context_timeframes": ["4h", "1w"],
    "expected_holding_horizon": "1–4 weeks (7–28 bars)",
    "minimum_data_requirements": 60,
    "volatility_policy": "Macro cycle regime classification.",
    "structure_requirement": "Macro daily support/resistance levels and multi-month trendlines.",
    "signal_evaluation_behavior": "Long-duration trend alignment; tolerates short-term multi-day pullbacks.",
    "entry_planning_context": "Macro equilibrium entries with wide structural stop loss protection.",
    "research_validation_requirements": "Long-term forward return distribution (5C, 10C, 20C).",
    "cost_sensitivity_bps": [0, 5, 10],
    "status": ProfileLifecycleStatus.APPROVED_FOR_ANALYTICAL_USE,
}
POSITION_1D_CONFIG = TradingProfileConfig(
    **_position_dict,
    config_hash=compute_profile_config_hash(_position_dict),
)

ALL_PROFILE_CONFIGS: Dict[str, TradingProfileConfig] = {
    PROFILE_SCALP_1M: SCALP_1M_CONFIG,
    PROFILE_INTRADAY_5M: INTRADAY_5M_CONFIG,
    PROFILE_TRADING_15M: TRADING_15M_CONFIG,
    PROFILE_SWING_4H: SWING_4H_CONFIG,
    PROFILE_POSITION_1D: POSITION_1D_CONFIG,
}
