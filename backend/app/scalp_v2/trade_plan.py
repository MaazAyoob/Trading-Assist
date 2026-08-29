"""
SCALP_STRATEGY_V2 — Trade Plan and Risk Management.
Generates scalping entry zones, structural stops, and strictly ordered R-multiple take profits.
"""
from typing import List, Tuple, Optional
from app.data.schema import Candle
from app.indicators.base import IndicatorSnapshot
from app.scalp_v2.config import (
    TP1_R_MULTIPLE,
    TP2_R_MULTIPLE,
    TP3_R_MULTIPLE,
    SL_ATR_MULTIPLIER,
    ENTRY_ZONE_ATR_FRACTION,
)
from app.scalp_v2.models import (
    ScalpV2Direction,
    ScalpV2TradeState,
    ScalpV2Lifecycle,
    ScalpV2Entry,
    ScalpV2StopLoss,
    ScalpV2TakeProfits,
)


def generate_scalp_v2_trade_plan(
    candles_1m: List[Candle],
    snap_1m: IndicatorSnapshot,
    direction: ScalpV2Direction,
) -> Tuple[ScalpV2TradeState, ScalpV2Lifecycle, ScalpV2Entry, ScalpV2StopLoss, ScalpV2TakeProfits, List[str]]:
    """
    Generate tight entry zone, structural stop loss, and R-multiple take profit targets.
    """
    if not candles_1m or direction in (ScalpV2Direction.NO_TRADE, ScalpV2Direction.WATCH):
        trade_state = ScalpV2TradeState.WATCH if direction == ScalpV2Direction.WATCH else ScalpV2TradeState.NO_TRADE
        return (
            trade_state,
            ScalpV2Lifecycle.WAITING,
            ScalpV2Entry(),
            ScalpV2StopLoss(),
            ScalpV2TakeProfits(),
            ["No active directional trade setup at this candle."],
        )

    current_candle = candles_1m[-1]
    close = current_candle.close
    atr = snap_1m.volatility.atr if (snap_1m.volatility and snap_1m.volatility.atr and snap_1m.volatility.atr > 0) else (close * 0.001)

    lookback = min(len(candles_1m), 10)
    recent_candles = candles_1m[-lookback:]

    if direction == ScalpV2Direction.BUY:
        trade_state = ScalpV2TradeState.BUY
        lifecycle = ScalpV2Lifecycle.ENTRY_READY
        planned_entry = close
        entry_zone_low = round(planned_entry - (atr * ENTRY_ZONE_ATR_FRACTION), 2)
        entry_zone_high = round(planned_entry + (atr * ENTRY_ZONE_ATR_FRACTION * 0.5), 2)

        # Stop loss: structural recent swing low with small buffer or ATR stop
        recent_low = min(c.low for c in recent_candles)
        sl_candidate = min(recent_low - (atr * 0.1), planned_entry - (atr * SL_ATR_MULTIPLIER))
        # Ensure SL is strictly below planned entry
        if sl_candidate >= planned_entry:
            sl_candidate = planned_entry - (atr * SL_ATR_MULTIPLIER)

        stop_loss_price = round(sl_candidate, 2)
        risk_distance = max(round(planned_entry - stop_loss_price, 2), 0.01)
        risk_atr = round(risk_distance / atr, 2) if atr > 0 else 1.0

        # Take Profits: Strictly ordered Entry < TP1 < TP2 < TP3
        tp1 = round(planned_entry + (risk_distance * TP1_R_MULTIPLE), 2)
        tp2 = round(planned_entry + (risk_distance * TP2_R_MULTIPLE), 2)
        tp3 = round(planned_entry + (risk_distance * TP3_R_MULTIPLE), 2)

        entry_model = ScalpV2Entry(
            planned_entry=planned_entry,
            entry_zone_low=entry_zone_low,
            entry_zone_high=entry_zone_high,
            reference_price=close,
        )
        sl_model = ScalpV2StopLoss(
            price=stop_loss_price,
            risk_distance=risk_distance,
            risk_distance_atr=risk_atr,
        )
        tp_model = ScalpV2TakeProfits(
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            rr_tp1=TP1_R_MULTIPLE,
            rr_tp2=TP2_R_MULTIPLE,
            rr_tp3=TP3_R_MULTIPLE,
        )

        invalidations = [
            f"1m Candle close below structural stop loss (${stop_loss_price:.2f})",
            "1m MACD histogram flips strongly negative",
            "5m Trend flips to confirmed bearish breakdown",
        ]

        return trade_state, lifecycle, entry_model, sl_model, tp_model, invalidations

    elif direction == ScalpV2Direction.SELL:
        trade_state = ScalpV2TradeState.SELL
        lifecycle = ScalpV2Lifecycle.ENTRY_READY
        planned_entry = close
        entry_zone_high = round(planned_entry + (atr * ENTRY_ZONE_ATR_FRACTION), 2)
        entry_zone_low = round(planned_entry - (atr * ENTRY_ZONE_ATR_FRACTION * 0.5), 2)

        # Stop loss: structural recent swing high with buffer or ATR stop
        recent_high = max(c.high for c in recent_candles)
        sl_candidate = max(recent_high + (atr * 0.1), planned_entry + (atr * SL_ATR_MULTIPLIER))
        # Ensure SL is strictly above planned entry
        if sl_candidate <= planned_entry:
            sl_candidate = planned_entry + (atr * SL_ATR_MULTIPLIER)

        stop_loss_price = round(sl_candidate, 2)
        risk_distance = max(round(stop_loss_price - planned_entry, 2), 0.01)
        risk_atr = round(risk_distance / atr, 2) if atr > 0 else 1.0

        # Take Profits: Strictly ordered TP3 < TP2 < TP1 < Entry
        tp1 = round(planned_entry - (risk_distance * TP1_R_MULTIPLE), 2)
        tp2 = round(planned_entry - (risk_distance * TP2_R_MULTIPLE), 2)
        tp3 = round(planned_entry - (risk_distance * TP3_R_MULTIPLE), 2)

        entry_model = ScalpV2Entry(
            planned_entry=planned_entry,
            entry_zone_low=entry_zone_low,
            entry_zone_high=entry_zone_high,
            reference_price=close,
        )
        sl_model = ScalpV2StopLoss(
            price=stop_loss_price,
            risk_distance=risk_distance,
            risk_distance_atr=risk_atr,
        )
        tp_model = ScalpV2TakeProfits(
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            rr_tp1=TP1_R_MULTIPLE,
            rr_tp2=TP2_R_MULTIPLE,
            rr_tp3=TP3_R_MULTIPLE,
        )

        invalidations = [
            f"1m Candle close above structural stop loss (${stop_loss_price:.2f})",
            "1m MACD histogram flips strongly positive",
            "5m Trend flips to confirmed bullish breakout",
        ]

        return trade_state, lifecycle, entry_model, sl_model, tp_model, invalidations

    trade_state = ScalpV2TradeState.NO_TRADE
    return trade_state, ScalpV2Lifecycle.WAITING, ScalpV2Entry(), ScalpV2StopLoss(), ScalpV2TakeProfits(), []
