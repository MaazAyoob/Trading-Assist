"""
Phase 10 — Trade Decision & Risk Planning Configuration.
Deterministic, auditable parameter definitions for trade planning and risk controls.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class TradeDecisionConfig(BaseModel):
    # Canonical R:R Multipliers
    default_tp1_r_multiple: float = Field(1.25, description="Canonical TP1 base risk multiple (1.25R)")
    default_tp2_r_multiple: float = Field(2.00, description="Canonical TP2 base risk multiple (2.00R)")
    default_tp3_r_multiple: float = Field(3.00, description="Canonical TP3 base risk multiple (3.00R)")

    # Strict Minimum Acceptable Risk-Reward Ratios
    min_acceptable_tp1_rr: float = Field(1.20, description="Minimum acceptable actual TP1 R:R (1.20)")
    min_acceptable_tp2_rr: float = Field(1.50, description="Minimum acceptable actual TP2 R:R (1.50)")
    min_acceptable_tp3_rr: float = Field(2.00, description="Minimum acceptable actual TP3 R:R (2.00)")

    # Structural Target Buffer
    structure_target_buffer_atr: float = Field(0.10, description="Deterministic ATR buffer for structural target adjustments (0.10 ATR)")

    # Stop Loss Sizing & Limits
    stop_atr_buffer: float = Field(0.50, description="ATR buffer beyond structural swing/zone level (0.50 ATR)")
    max_stop_distance_atr: float = Field(3.50, description="Maximum allowable stop distance in ATR units (3.50 ATR)")
    min_stop_distance_atr: float = Field(0.30, description="Minimum allowable stop distance in ATR units (0.30 ATR)")

    # Plan Validity & Expiration
    default_max_valid_candles: int = Field(12, description="Maximum closed candles a planned setup remains valid before expiring")

    # Alignment Score Thresholds
    min_alignment_score_actionable: float = Field(50.0, description="Minimum decision_alignment_score required for BUY/SELL setup")

    # Pullback & Breakout Sizing
    pullback_zone_atr_depth: float = Field(0.50, description="Depth of pullback entry zone in ATR units")
    breakout_buffer_atr: float = Field(0.10, description="Buffer above/below breakout level for entry reference")


# Global default configuration instance
DEFAULT_TRADE_DECISION_CONFIG = TradeDecisionConfig()
