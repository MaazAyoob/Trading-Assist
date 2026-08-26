"""
Version definitions and cryptographic configuration hashes for Phase 12 Trading Profiles.
"""

import hashlib
import json

PROFILES_FRAMEWORK_VERSION = "v1.0.0"

# Canonical profile IDs
PROFILE_SCALP_1M = "SCALP_1M_V1"
PROFILE_INTRADAY_5M = "INTRADAY_5M_V1"
PROFILE_TRADING_15M = "TRADING_15M_V1"
PROFILE_SWING_4H = "SWING_4H_V1"
PROFILE_POSITION_1D = "POSITION_1D_V1"

ALL_PROFILE_IDS = [
    PROFILE_SCALP_1M,
    PROFILE_INTRADAY_5M,
    PROFILE_TRADING_15M,
    PROFILE_SWING_4H,
    PROFILE_POSITION_1D,
]


def compute_profile_config_hash(config_dict: dict) -> str:
    """Computes a deterministic SHA256 configuration hash."""
    canonical_json = json.dumps(config_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:16]


PROFILES_CONFIG_HASH = "8f3b49c1e7a502d6"
