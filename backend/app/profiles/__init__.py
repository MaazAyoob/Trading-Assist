"""
Trading Profiles Framework Package.
Provides multi-timeframe profile orchestration over frozen analytical engines.
"""

from app.profiles.version import (
    PROFILES_FRAMEWORK_VERSION,
    PROFILES_CONFIG_HASH,
)
from app.profiles.models import (
    ProfileEnum,
    ProfileStateEnum,
    TradingProfileConfig,
    MultiTimeframeContext,
    CostSensitivityTier,
    ProfileAnalysisResult,
    ProfileComparisonReport,
)
from app.profiles.config import (
    SCALP_1M_CONFIG,
    INTRADAY_5M_CONFIG,
    TRADING_15M_CONFIG,
    SWING_4H_CONFIG,
    POSITION_1D_CONFIG,
    ALL_PROFILE_CONFIGS,
)
from app.profiles.registry import ProfileRegistry, profile_registry
from app.profiles.context import MultiTimeframeContextBuilder
from app.profiles.validation import ProfileValidator
from app.profiles.engine import TradingProfileEngine

__all__ = [
    "PROFILES_FRAMEWORK_VERSION",
    "PROFILES_CONFIG_HASH",
    "ProfileEnum",
    "ProfileStateEnum",
    "TradingProfileConfig",
    "MultiTimeframeContext",
    "CostSensitivityTier",
    "ProfileAnalysisResult",
    "ProfileComparisonReport",
    "SCALP_1M_CONFIG",
    "INTRADAY_5M_CONFIG",
    "TRADING_15M_CONFIG",
    "SWING_4H_CONFIG",
    "POSITION_1D_CONFIG",
    "ALL_PROFILE_CONFIGS",
    "ProfileRegistry",
    "profile_registry",
    "MultiTimeframeContextBuilder",
    "ProfileValidator",
    "TradingProfileEngine",
]
