"""
Unit tests for Profile Registry & Configuration Integrity.
"""

import pytest
from app.profiles.registry import profile_registry
from app.profiles.version import ALL_PROFILE_IDS


def test_profile_registry_integrity_and_hashes():
    assert profile_registry.validate_registry() is True
    profiles = profile_registry.list_profiles()
    assert len(profiles) == 5

    for p in profiles:
        assert p.profile_id in ALL_PROFILE_IDS
        assert len(p.config_hash) == 16
        assert len(p.context_timeframes) >= 1
        assert p.primary_timeframe in ("1m", "5m", "15m", "4h", "1d")


def test_profile_retrieval_by_timeframe():
    scalp = profile_registry.get_profile_by_timeframe("1m")
    assert scalp is not None
    assert scalp.profile_id == "SCALP_1M_V1"

    intraday = profile_registry.get_profile_by_timeframe("5m")
    assert intraday is not None
    assert intraday.profile_id == "INTRADAY_5M_V1"

    trading = profile_registry.get_profile_by_timeframe("15m")
    assert trading is not None
    assert trading.profile_id == "TRADING_15M_V1"

    swing = profile_registry.get_profile_by_timeframe("4h")
    assert swing is not None
    assert swing.profile_id == "SWING_4H_V1"

    position = profile_registry.get_profile_by_timeframe("1d")
    assert position is not None
    assert position.profile_id == "POSITION_1D_V1"
