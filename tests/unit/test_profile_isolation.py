"""
Unit tests for Profile Isolation & Zero Exchange Execution Security Audit.
"""

import pytest
import inspect
from app.profiles.registry import profile_registry
import app.profiles.engine
import app.profiles.context


def test_profiles_isolated_instances():
    scalp = profile_registry.get_profile("SCALP_1M_V1")
    swing = profile_registry.get_profile("SWING_4H_V1")

    assert scalp.profile_id != swing.profile_id
    assert scalp.primary_timeframe != swing.primary_timeframe
    assert scalp.config_hash != swing.config_hash


def test_security_audit_zero_exchange_trading_in_profiles():
    """Verify zero live trading, order placement, or exchange execution imports exist in profiles."""
    for mod in [app.profiles.engine, app.profiles.context, app.profiles.registry]:
        source = inspect.getsource(mod)
        for forbidden in ["ccxt", "binance.client", "place_order", "create_order", "api_key", "secret_key"]:
            assert forbidden not in source.lower(), f"Forbidden trading term '{forbidden}' detected in {mod}!"
