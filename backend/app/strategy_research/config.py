"""
Phase 8 — Strategy Research Configuration & Predefined Hypotheses.
Strict anti-overfitting configurations: zero brute-force parameter grids.
"""

from typing import Dict, Any

STRATEGY_BASELINE = "PHASE5_V0.5.0"
BASELINE_CONFIG_VERSION = "2026-08-24-v1"
DATASET_SHA256 = "0c65f8e364cb1b4cc21c821c9a2a5f2977ae189d370d9e4eb7e6da31be850b6c"

# Chronological partition bounds (UTC milliseconds)
TRAIN_START = 1704067200000      # 2024-01-01 00:00:00 UTC
TRAIN_END = 1735689599999        # 2024-12-31 23:45:00 UTC
VAL_START = 1735689600000        # 2025-01-01 00:00:00 UTC
VAL_END = 1751327999999          # 2025-06-30 23:45:00 UTC
TEST_START = 1751328000000       # 2025-07-01 00:00:00 UTC
TEST_END = 1767226499999         # 2025-12-31 23:45:00 UTC

# Predeclared Research Hypotheses & Discrete Candidates
EXPERIMENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "EXP_A1_PULLBACK_EMA21": {
        "name": "Experiment A1 — Pullback-Aware Entry (21 EMA)",
        "description": "Requires price to temporarily retrace within 0.5 ATR of the 21 EMA while broader trend remains intact before generating a signal.",
        "hypothesis": "Demanding a pullback toward the 21 EMA avoids buying/selling at local impulse extremes and improves entry timeliness.",
        "parameters": {
            "reference_indicator": "EMA_21",
            "max_distance_atr": 0.75,
            "min_pullback_bars": 1,
            "require_trend_intact": True,
        },
    },
    "EXP_A2_PULLBACK_VWAP": {
        "name": "Experiment A2 — Pullback-Aware Entry (Rolling VWAP)",
        "description": "Requires price to retrace toward the 24-period Rolling VWAP within 0.75 ATR before setup generation.",
        "hypothesis": "VWAP serves as dynamic institutional equilibrium; entering near VWAP avoids chasing extended prices.",
        "parameters": {
            "reference_indicator": "VWAP",
            "max_distance_atr": 0.75,
            "min_pullback_bars": 1,
            "require_trend_intact": True,
        },
    },
    "EXP_B1_DIVERGENCE_RSI": {
        "name": "Experiment B1 — Momentum Divergence (RSI)",
        "description": "Suppresses trend signals if classical RSI divergence is detected (e.g. Higher High in price with Lower High in RSI).",
        "hypothesis": "Filtering signals with active momentum divergence eliminates late-stage trend exhaustion setups.",
        "parameters": {
            "divergence_source": "RSI_14",
            "lookback_swings": 2,
            "suppress_exhaustion": True,
        },
    },
    "EXP_B2_DIVERGENCE_MACD": {
        "name": "Experiment B2 — Momentum Divergence (MACD Histogram)",
        "description": "Filters setups if MACD histogram fails to confirm higher highs in price.",
        "hypothesis": "MACD histogram deceleration flags momentum exhaustion before structural reversal.",
        "parameters": {
            "divergence_source": "MACD_HIST",
            "lookback_swings": 2,
            "suppress_exhaustion": True,
        },
    },
    "EXP_C1_FIRST_STRUCTURAL_EVENT": {
        "name": "Experiment C1 — First Structural Event in Sequence",
        "description": "Permits setup generation only on the first initial confirmation following a confirmed BOS/CHoCH event, suppressing subsequent repeat triggers.",
        "hypothesis": "Restricting setups to the first valid post-breakout bar eliminates redundant trailing trend signals and reduces clustering.",
        "parameters": {
            "max_bars_post_breakout": 3,
            "require_fresh_event": True,
            "allow_retrigger_without_new_structure": False,
        },
    },
    "EXP_D1_EPISODE_COOLDOWN": {
        "name": "Experiment D1 — One Setup Per Structural Episode",
        "description": "Consolidates continuous directional persistence runs into a single entry setup per structural episode.",
        "hypothesis": "The 69% adjacent clustering is an artifact of bar-by-bar classification; episode consolidation isolates true independent market setups.",
        "parameters": {
            "max_setups_per_episode": 1,
            "reset_on_direction_change": True,
            "reset_on_choch": True,
        },
    },
    "EXP_E1_EXTENSION_FILTER_EMA21": {
        "name": "Experiment E1 — Extension Filter (21 EMA > 1.5 ATR)",
        "description": "Suppresses setups when price is extended more than 1.5 ATR away from the 21 EMA.",
        "hypothesis": "Large price-to-EMA standard deviations represent mean-reversion risk rather than sustainable impulse continuation.",
        "parameters": {
            "extension_metric": "EMA21_DISTANCE_ATR",
            "max_allowed_extension_atr": 1.5,
        },
    },
    "EXP_E2_EXTENSION_FILTER_VWAP": {
        "name": "Experiment E2 — Extension Filter (VWAP > 1.75 ATR)",
        "description": "Suppresses setups when price is extended more than 1.75 ATR away from Rolling VWAP.",
        "hypothesis": "Extreme deviations from rolling VWAP signal institutional over-extension.",
        "parameters": {
            "extension_metric": "VWAP_DISTANCE_ATR",
            "max_allowed_extension_atr": 1.75,
        },
    },
    "EXP_F1_COMBINED_CANDIDATE": {
        "name": "Experiment F1 — Synthesized Causal Strategy Candidate",
        "description": "Combines First-Structural-Event eligibility + 21 EMA Pullback + Extension Cap + One-Setup-Per-Episode.",
        "hypothesis": "Combining structural timing with pullback discipline and extension suppression eliminates trend-chasing while improving post-signal returns.",
        "parameters": {
            "first_structural_event": True,
            "pullback_ema21_max_atr": 1.0,
            "extension_cap_atr": 1.5,
            "one_setup_per_episode": True,
            "suppress_rsi_divergence": True,
        },
    },
}
