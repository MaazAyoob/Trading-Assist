"""
Profile Registry for Phase 12.
Provides static registration, retrieval, and validation of trading profiles.
"""

from typing import Dict, List, Optional
from app.profiles.models import TradingProfileConfig
from app.profiles.config import ALL_PROFILE_CONFIGS
from app.profiles.version import (
    PROFILE_SCALP_1M,
    PROFILE_INTRADAY_5M,
    PROFILE_TRADING_15M,
    PROFILE_SWING_4H,
    PROFILE_POSITION_1D,
)


class ProfileRegistry:
    def __init__(self, profiles: Optional[Dict[str, TradingProfileConfig]] = None):
        self._profiles: Dict[str, TradingProfileConfig] = profiles or ALL_PROFILE_CONFIGS.copy()

    def get_profile(self, profile_id: str) -> Optional[TradingProfileConfig]:
        """Retrieve profile by unique profile_id."""
        return self._profiles.get(profile_id)

    def get_profile_by_timeframe(self, primary_tf: str) -> Optional[TradingProfileConfig]:
        """Find matching profile for a given primary timeframe."""
        tf_mapping = {
            "1m": PROFILE_SCALP_1M,
            "5m": PROFILE_INTRADAY_5M,
            "15m": PROFILE_TRADING_15M,
            "4h": PROFILE_SWING_4H,
            "1d": PROFILE_POSITION_1D,
        }
        target_id = tf_mapping.get(primary_tf)
        if target_id and target_id in self._profiles:
            return self._profiles[target_id]
        return None

    def list_profiles(self) -> List[TradingProfileConfig]:
        """List all registered trading profiles in canonical order."""
        order = [
            PROFILE_SCALP_1M,
            PROFILE_INTRADAY_5M,
            PROFILE_TRADING_15M,
            PROFILE_SWING_4H,
            PROFILE_POSITION_1D,
        ]
        return [self._profiles[pid] for pid in order if pid in self._profiles]

    def validate_registry(self) -> bool:
        """Validates that all expected profiles are present and contain valid hashes."""
        required = [
            PROFILE_SCALP_1M,
            PROFILE_INTRADAY_5M,
            PROFILE_TRADING_15M,
            PROFILE_SWING_4H,
            PROFILE_POSITION_1D,
        ]
        for pid in required:
            if pid not in self._profiles:
                return False
            cfg = self._profiles[pid]
            if not cfg.config_hash or len(cfg.config_hash) != 16:
                return False
        return True


# Global singleton instance
profile_registry = ProfileRegistry()
