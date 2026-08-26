"""
Phase 9 — Shadow Validation Configuration & Immutable Hashes.
Calculates frozen configuration hashes and sets research evaluation constants.
"""

import hashlib
import json
from typing import Dict, Any

HORIZONS = [1, 3, 5, 10, 20]
COST_TIERS_BPS = [0, 5, 10]

CANDIDATES = {
    "BASELINE": {
        "name": "Phase 5 Multi-Factor Baseline (v0.5.0)",
        "version": "0.5.0",
        "config_version": "2026-08-24-v1",
        "type": "BASELINE",
    },
    "EXP_A2_PULLBACK_VWAP": {
        "name": "Experiment A2 — Pullback-Aware Entry (Rolling VWAP)",
        "version": "0.8.0-research",
        "config_version": "EXP_A2_VWAP_PULLBACK_V1",
        "reference_indicator": "VWAP",
        "max_distance_atr": 0.75,
        "type": "CANDIDATE_FOR_PAPER_TRADING",
    },
    "EXP_E2_EXTENSION_VWAP": {
        "name": "Experiment E2 — Extension Filter (VWAP > 1.75 ATR)",
        "version": "0.8.0-research",
        "config_version": "EXP_E2_VWAP_EXTENSION_V1",
        "extension_metric": "VWAP_DISTANCE_ATR",
        "max_allowed_extension_atr": 1.75,
        "type": "CANDIDATE_FOR_PAPER_TRADING",
    },
}

# Historical Phase 8 Benchmarks for Observational Drift Comparison
HISTORICAL_BENCHMARKS = {
    "BASELINE": {
        "validation_5c_median": -0.00033,
        "validation_5c_pos_rate": 45.9,
        "test_5c_median": -0.00053,
        "test_5c_pos_rate": 42.9,
        "adjacent_clustering": 69.9,
    },
    "EXP_A2_PULLBACK_VWAP": {
        "validation_5c_median": +0.00101,
        "validation_5c_pos_rate": 57.8,
        "test_5c_median": +0.00009,
        "test_5c_pos_rate": 50.0,
        "adjacent_clustering": 21.4,
    },
    "EXP_E2_EXTENSION_VWAP": {
        "validation_5c_median": -0.00002,
        "validation_5c_pos_rate": 49.6,
        "test_5c_median": +0.00003,
        "test_5c_pos_rate": 48.6,
        "adjacent_clustering": 43.5,
    },
}


def compute_frozen_configuration_hashes() -> Dict[str, str]:
    """Generates immutable SHA-256 hashes of all system engine and candidate configurations."""
    hashes = {}

    # Signal Engine / Baseline Config Hash
    base_blob = json.dumps(CANDIDATES["BASELINE"], sort_keys=True).encode("utf-8")
    hashes["phase5_signal_engine_hash"] = hashlib.sha256(base_blob).hexdigest()

    # A2 Candidate Config Hash
    a2_blob = json.dumps(CANDIDATES["EXP_A2_PULLBACK_VWAP"], sort_keys=True).encode("utf-8")
    hashes["candidate_a2_config_hash"] = hashlib.sha256(a2_blob).hexdigest()

    # E2 Candidate Config Hash
    e2_blob = json.dumps(CANDIDATES["EXP_E2_EXTENSION_VWAP"], sort_keys=True).encode("utf-8")
    hashes["candidate_e2_config_hash"] = hashlib.sha256(e2_blob).hexdigest()

    # System Constants Hash
    sys_blob = json.dumps({"horizons": HORIZONS, "cost_tiers": COST_TIERS_BPS}, sort_keys=True).encode("utf-8")
    hashes["shadow_validation_system_hash"] = hashlib.sha256(sys_blob).hexdigest()

    return hashes
