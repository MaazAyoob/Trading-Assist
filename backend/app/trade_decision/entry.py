"""
Phase 10 — Deterministic Entry Planner.
Calculates rule-based analytical entry references, planned entry prices, and entry zones.
Never fabricates arbitrary entry prices.
"""

from typing import Optional, Tuple
from app.data.schema import Candle
from app.indicators.base import IndicatorSnapshot
from app.structure.models import MarketStructureSnapshot
from app.signals.models import ResearchSignal, SignalDirectionEnum
from app.trade_decision.config import TradeDecisionConfig, DEFAULT_TRADE_DECISION_CONFIG
from app.trade_decision.models import EntryPlan, EntryTypeEnum, TradePlanState


class EntryPlanner:
    """
    Deterministic rule-based entry planner.
    Computes unambiguous planned_entry_price and entry zone bounds based on closed candles,
    VWAP, EMA 21, ATR, and confirmed market structure.
    """

    @staticmethod
    def plan_entry(
        candle: Candle,
        indicators: IndicatorSnapshot,
        structure: MarketStructureSnapshot,
        signal: ResearchSignal,
        config: TradeDecisionConfig = DEFAULT_TRADE_DECISION_CONFIG,
    ) -> Optional[Tuple[EntryPlan, TradePlanState]]:
        """
        Determines a rule-based analytical entry reference and corresponding TradePlanState.
        Returns None if no reasonable entry structure can be established.
        """
        if candle is None or indicators is None or indicators.volatility is None or indicators.volatility.atr is None or indicators.volatility.atr <= 0:
            return None

        ref_price = float(candle.close)
        atr = float(indicators.volatility.atr)
        ema_21 = float(indicators.trend.ema_21) if (indicators.trend and indicators.trend.ema_21 is not None) else ref_price
        vwap = float(indicators.trend.vwap) if (indicators.trend and indicators.trend.vwap is not None) else ref_price

        direction = signal.direction

        if direction == SignalDirectionEnum.LONG_SETUP:
            # 1. Check for Breakout Reference (recent confirmed BOS high on this bar or immediate prior bar)
            recent_bullish_bos = structure.bos_events[-1] if structure.bos_events and structure.bos_events[-1].event_type.value == "BULLISH_BOS" else None
            if (
                recent_bullish_bos
                and structure.active_structural_high
            ):
                sh_price = float(structure.active_structural_high.price)
                if abs(ref_price - sh_price) <= 1.5 * atr:
                    planned_entry = round(sh_price + config.breakout_buffer_atr * atr, 4)
                    zone_low = round(sh_price, 4)
                    zone_high = round(planned_entry + 0.2 * atr, 4)
                    entry_type = EntryTypeEnum.BREAKOUT_REFERENCE
                    desc = f"Bullish breakout reference above confirmed swing high (${sh_price:,.2f}) + {config.breakout_buffer_atr:.2f} ATR buffer."
                    state = TradePlanState.ENTRY_ZONE_ACTIVE if (zone_low <= ref_price <= zone_high) else TradePlanState.WAITING_FOR_ENTRY
                    return EntryPlan(
                        reference_price=ref_price,
                        planned_entry_price=planned_entry,
                        entry_type=entry_type,
                        entry_zone_low=zone_low,
                        entry_zone_high=zone_high,
                        formula_description=desc,
                    ), state

            # 2. Check for Pullback Zone (preferred if price is extended above EMA/VWAP)
            support_ref = None
            if structure.support_zones:
                # Find nearest unviolated support below or near reference price
                nearby_supports = [sz for sz in structure.support_zones if sz.price_center <= ref_price + 0.5 * atr]
                if nearby_supports:
                    support_ref = float(nearby_supports[0].price_center)

            # Zone bounds around dynamic equilibrium (VWAP / EMA 21 / Support)
            anchor_mid = (ema_21 + vwap) / 2.0
            if support_ref is not None and abs(support_ref - anchor_mid) < 1.0 * atr:
                anchor_mid = (anchor_mid + support_ref) / 2.0

            if ref_price > anchor_mid + 0.3 * atr:
                # Price is extended above equilibrium: establish Pullback Zone
                zone_high = round(min(ref_price, anchor_mid + 0.3 * atr), 4)
                zone_low = round(max(anchor_mid - config.pullback_zone_atr_depth * atr, zone_high - 0.6 * atr), 4)
                if zone_low >= zone_high:
                    zone_low = round(zone_high - 0.4 * atr, 4)
                planned_entry = round((zone_low + zone_high) / 2.0, 4)
                entry_type = EntryTypeEnum.PULLBACK_ZONE
                desc = f"Pullback zone towards dynamic mean (VWAP: ${vwap:,.2f}, EMA 21: ${ema_21:,.2f})."
                state = TradePlanState.ENTRY_ZONE_ACTIVE if (zone_low <= ref_price <= zone_high) else TradePlanState.WAITING_FOR_ENTRY
                return EntryPlan(
                    reference_price=ref_price,
                    planned_entry_price=planned_entry,
                    entry_type=entry_type,
                    entry_zone_low=zone_low,
                    entry_zone_high=zone_high,
                    formula_description=desc,
                ), state
            else:
                # Price is sitting at equilibrium: Market Reference
                planned_entry = round(ref_price, 4)
                zone_low = round(ref_price - 0.2 * atr, 4)
                zone_high = round(ref_price + 0.2 * atr, 4)
                entry_type = EntryTypeEnum.MARKET_REFERENCE
                desc = f"Market reference entry at confirmed close equilibrium (${ref_price:,.2f})."
                state = TradePlanState.ENTRY_ZONE_ACTIVE
                return EntryPlan(
                    reference_price=ref_price,
                    planned_entry_price=planned_entry,
                    entry_type=entry_type,
                    entry_zone_low=zone_low,
                    entry_zone_high=zone_high,
                    formula_description=desc,
                ), state

        elif direction == SignalDirectionEnum.SHORT_SETUP:
            # 1. Check for Breakdown Reference (recent confirmed BOS low)
            recent_bearish_bos = structure.bos_events[-1] if structure.bos_events and structure.bos_events[-1].event_type.value == "BEARISH_BOS" else None
            if (
                recent_bearish_bos
                and structure.active_structural_low
            ):
                sl_price = float(structure.active_structural_low.price)
                if abs(ref_price - sl_price) <= 1.5 * atr:
                    planned_entry = round(sl_price - config.breakout_buffer_atr * atr, 4)
                    zone_high = round(sl_price, 4)
                    zone_low = round(planned_entry - 0.2 * atr, 4)
                    entry_type = EntryTypeEnum.BREAKOUT_REFERENCE
                    desc = f"Bearish breakdown reference below confirmed swing low (${sl_price:,.2f}) - {config.breakout_buffer_atr:.2f} ATR buffer."
                    state = TradePlanState.ENTRY_ZONE_ACTIVE if (zone_low <= ref_price <= zone_high) else TradePlanState.WAITING_FOR_ENTRY
                    return EntryPlan(
                        reference_price=ref_price,
                        planned_entry_price=planned_entry,
                        entry_type=entry_type,
                        entry_zone_low=zone_low,
                        entry_zone_high=zone_high,
                        formula_description=desc,
                    ), state

            # 2. Check for Retracement / Pullback Zone for Shorts
            res_ref = None
            if structure.resistance_zones:
                nearby_res = [rz for rz in structure.resistance_zones if rz.price_center >= ref_price - 0.5 * atr]
                if nearby_res:
                    res_ref = float(nearby_res[0].price_center)

            anchor_mid = (ema_21 + vwap) / 2.0
            if res_ref is not None and abs(res_ref - anchor_mid) < 1.0 * atr:
                anchor_mid = (anchor_mid + res_ref) / 2.0

            if ref_price < anchor_mid - 0.3 * atr:
                # Price is extended below equilibrium: establish Retracement Zone
                zone_low = round(max(ref_price, anchor_mid - 0.3 * atr), 4)
                zone_high = round(min(anchor_mid + config.pullback_zone_atr_depth * atr, zone_low + 0.6 * atr), 4)
                if zone_high <= zone_low:
                    zone_high = round(zone_low + 0.4 * atr, 4)
                planned_entry = round((zone_low + zone_high) / 2.0, 4)
                entry_type = EntryTypeEnum.PULLBACK_ZONE
                desc = f"Retracement zone towards dynamic mean (VWAP: ${vwap:,.2f}, EMA 21: ${ema_21:,.2f})."
                state = TradePlanState.ENTRY_ZONE_ACTIVE if (zone_low <= ref_price <= zone_high) else TradePlanState.WAITING_FOR_ENTRY
                return EntryPlan(
                    reference_price=ref_price,
                    planned_entry_price=planned_entry,
                    entry_type=entry_type,
                    entry_zone_low=zone_low,
                    entry_zone_high=zone_high,
                    formula_description=desc,
                ), state
            else:
                # Market Reference
                planned_entry = round(ref_price, 4)
                zone_low = round(ref_price - 0.2 * atr, 4)
                zone_high = round(ref_price + 0.2 * atr, 4)
                entry_type = EntryTypeEnum.MARKET_REFERENCE
                desc = f"Market reference entry at confirmed close equilibrium (${ref_price:,.2f})."
                state = TradePlanState.ENTRY_ZONE_ACTIVE
                return EntryPlan(
                    reference_price=ref_price,
                    planned_entry_price=planned_entry,
                    entry_type=entry_type,
                    entry_zone_low=zone_low,
                    entry_zone_high=zone_high,
                    formula_description=desc,
                ), state

        return None
