"""
Phase 10 — Deterministic Stop Loss Planner.
Calculates structural stop-loss levels anchored to confirmed swing extremes, support/resistance zones,
and ATR safety buffers. Rejects mathematically invalid or excessive-risk stops.
"""

from typing import Optional
from app.indicators.base import IndicatorSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.models import SignalDirectionEnum
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import StopLossPlan


class StopLossPlanner:
    """
    Deterministic Stop Loss Planner.
    Calculates structural stop loss from planned_entry_price using swing points, S/R zones, and ATR buffer.
    Strictly validates stop placement direction and distance sanity.
    """

    @staticmethod
    def plan_stop_loss(
        planned_entry_price: float,
        direction: SignalDirectionEnum,
        indicators: IndicatorSnapshot,
        structure: MarketStructureSnapshot,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> Optional[StopLossPlan]:
        """
        Calculates StopLossPlan for a given planned_entry_price.
        Returns None if stop placement is invalid, contradictory, or exceeds risk bounds.
        """
        if planned_entry_price <= 0 or indicators is None or indicators.volatility is None or indicators.volatility.atr is None or indicators.volatility.atr <= 0:
            return None

        atr = float(indicators.volatility.atr)
        buffer = config.stop_atr_buffer

        if direction == SignalDirectionEnum.LONG_SETUP:
            structural_level: Optional[float] = None
            reason: str = ""

            # 1. Check confirmed active structural low below planned entry
            if structure.active_structural_low and structure.active_structural_low.price < planned_entry_price:
                structural_level = float(structure.active_structural_low.price)
                reason = f"Confirmed structural swing low at ${structural_level:,.2f} with {buffer:.2f} ATR protective buffer."

            # 2. Check support zones below planned entry if no structural low or if support is closer/cleaner
            elif structure.support_zones:
                valid_supports = [sz.price_low for sz in structure.support_zones if sz.price_low < planned_entry_price]
                if valid_supports:
                    structural_level = float(valid_supports[0])
                    reason = f"Confirmed support zone boundary at ${structural_level:,.2f} with {buffer:.2f} ATR protective buffer."

            # 3. Fallback: Pure ATR protective stop
            if structural_level is None:
                structural_level = planned_entry_price - 1.0 * atr
                reason = f"ATR protective stop level (1.0 ATR baseline + {buffer:.2f} ATR buffer)."

            raw_stop = structural_level - (buffer * atr)
            raw_stop = round(raw_stop, 4)

            # Strict Direction Invariant: BUY SL must be strictly below planned entry
            if raw_stop >= planned_entry_price:
                return None

            distance = round(planned_entry_price - raw_stop, 4)
            distance_atr = round(distance / atr, 4)

            # Clamp minimum stop distance if too tight (< min_stop_distance_atr)
            if distance_atr < config.min_stop_distance_atr:
                raw_stop = round(planned_entry_price - (config.min_stop_distance_atr * atr), 4)
                distance = round(planned_entry_price - raw_stop, 4)
                distance_atr = round(distance / atr, 4)
                reason += f" (Enforced minimum {config.min_stop_distance_atr:.2f} ATR distance)."

            # Reject if stop distance exceeds maximum allowable risk limit
            if distance_atr > config.max_stop_distance_atr:
                return None

            return StopLossPlan(
                price=raw_stop,
                distance=distance,
                distance_atr=distance_atr,
                reason=reason,
                structural_reference_level=round(structural_level, 4) if structural_level else None,
                atr_buffer_used=buffer,
            )

        elif direction == SignalDirectionEnum.SHORT_SETUP:
            structural_level = None
            reason = ""

            # 1. Check confirmed active structural high above planned entry
            if structure.active_structural_high and structure.active_structural_high.price > planned_entry_price:
                structural_level = float(structure.active_structural_high.price)
                reason = f"Confirmed structural swing high at ${structural_level:,.2f} with {buffer:.2f} ATR protective buffer."

            # 2. Check resistance zones above planned entry
            elif structure.resistance_zones:
                valid_res = [rz.price_high for rz in structure.resistance_zones if rz.price_high > planned_entry_price]
                if valid_res:
                    structural_level = float(valid_res[0])
                    reason = f"Confirmed resistance zone boundary at ${structural_level:,.2f} with {buffer:.2f} ATR protective buffer."

            # 3. Fallback: Pure ATR protective stop
            if structural_level is None:
                structural_level = planned_entry_price + 1.0 * atr
                reason = f"ATR protective stop level (1.0 ATR baseline + {buffer:.2f} ATR buffer)."

            raw_stop = structural_level + (buffer * atr)
            raw_stop = round(raw_stop, 4)

            # Strict Direction Invariant: SELL SL must be strictly above planned entry
            if raw_stop <= planned_entry_price:
                return None

            distance = round(raw_stop - planned_entry_price, 4)
            distance_atr = round(distance / atr, 4)

            # Clamp minimum stop distance if too tight (< min_stop_distance_atr)
            if distance_atr < config.min_stop_distance_atr:
                raw_stop = round(planned_entry_price + (config.min_stop_distance_atr * atr), 4)
                distance = round(raw_stop - planned_entry_price, 4)
                distance_atr = round(distance / atr, 4)
                reason += f" (Enforced minimum {config.min_stop_distance_atr:.2f} ATR distance)."

            # Reject if stop distance exceeds maximum allowable risk limit
            if distance_atr > config.max_stop_distance_atr:
                return None

            return StopLossPlan(
                price=raw_stop,
                distance=distance,
                distance_atr=distance_atr,
                reason=reason,
                structural_reference_level=round(structural_level, 4) if structural_level else None,
                atr_buffer_used=buffer,
            )

        return None
