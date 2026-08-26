import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.trade_decision.engine import TradeDecisionEngine
from app.trade_decision.models import TradeDecisionEnum

def create_bullish_candles(num_cycles: int = 15):
    candles = []
    base_price = 50000.0
    t = 1700000000000

    for k in range(num_cycles):
        peak_base = base_price + k * 250.0
        for j in range(5):
            close = peak_base + j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close - spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        if k < num_cycles - 1:
            top_close = candles[-1].close
            for j in range(1, 5):
                close = top_close - j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close + spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles

def create_bearish_candles(num_cycles: int = 15):
    candles = []
    base_price = 50000.0
    t = 1700000000000

    for k in range(num_cycles):
        trough_base = base_price - k * 250.0
        for j in range(5):
            close = trough_base - j * 50.0
            spread = close * 0.002
            candles.append(
                Candle(
                    timestamp=t,
                    open=close + spread * 0.5,
                    high=close + spread,
                    low=close - spread,
                    close=close,
                    volume=200.0 + k * 10.0 + j * 20.0,
                    close_time=t + 899999,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
            t += 900000
        if k < num_cycles - 1:
            bot_close = candles[-1].close
            for j in range(1, 5):
                close = bot_close + j * 30.0
                spread = close * 0.002
                candles.append(
                    Candle(
                        timestamp=t,
                        open=close - spread * 0.5,
                        high=close + spread,
                        low=close - spread,
                        close=close,
                        volume=80.0,
                        close_time=t + 899999,
                        is_closed=True,
                        state=CandleStateEnum.CLOSED,
                    )
                )
                t += 900000
    return candles

def main():
    print("=== SCENARIO 1: BULLISH CANDLES ===")
    b_candles = create_bullish_candles(15)
    quality = MarketDataQuality(symbol="BTCUSDT", timeframe="15m", status=QualityStatusEnum.HEALTHY, candle_count=len(b_candles), is_reliable=True)
    ind = IndicatorEngine.calculate_snapshot(b_candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    struct = MarketStructureEngine.evaluate(b_candles, indicators=ind, is_confirmed=True)
    regime = MarketRegimeEngine.classify(candles=b_candles, indicators=ind, structure_state=struct.structure_direction, is_confirmed=True)
    signal = MultiFactorSignalEngine.calculate_signal(candles=b_candles, indicators=ind, regime=regime, structure=struct, is_confirmed=True)

    plan_buy = TradeDecisionEngine.calculate_decision(
        candles=b_candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        signal=signal,
        quality=quality,
        strategy_context_id="PHASE5_BASELINE",
        is_confirmed=True,
    )
    print(f"Candle Timestamp: {b_candles[-1].timestamp} ({b_candles[-1].close})")
    print(f"Signal: {signal.direction} (Score: {signal.score})")
    print(f"Decision: {plan_buy.decision}")
    print(f"State: {plan_buy.state}")
    print(f"Alignment Score: {plan_buy.decision_alignment_score}")
    if plan_buy.entry:
        print(f"Planned Entry: {plan_buy.entry.planned_entry_price} (Zone: {plan_buy.entry.entry_zone_low} - {plan_buy.entry.entry_zone_high})")
        print(f"Stop Loss: {plan_buy.stop_loss.price} (Risk: ${plan_buy.stop_loss.distance:.2f}, {plan_buy.stop_loss.distance_atr:.2f} ATR)")
        print(f"TP1: {plan_buy.take_profits.tp1.adjusted_target} (RR: {plan_buy.take_profits.tp1.actual_rr_after_adjustment:.2f}R)")
        print(f"TP2: {plan_buy.take_profits.tp2.adjusted_target} (RR: {plan_buy.take_profits.tp2.actual_rr_after_adjustment:.2f}R)")
        print(f"TP3: {plan_buy.take_profits.tp3.adjusted_target} (RR: {plan_buy.take_profits.tp3.actual_rr_after_adjustment:.2f}R)")
    else:
        print(f"Reasons for NO_TRADE: {plan_buy.reasons_for_no_trade}")

    print("\n=== SCENARIO 2: BEARISH CANDLES ===")
    s_candles = create_bearish_candles(15)
    s_ind = IndicatorEngine.calculate_snapshot(s_candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    s_struct = MarketStructureEngine.evaluate(s_candles, indicators=s_ind, is_confirmed=True)
    s_regime = MarketRegimeEngine.classify(candles=s_candles, indicators=s_ind, structure_state=s_struct.structure_direction, is_confirmed=True)
    s_signal = MultiFactorSignalEngine.calculate_signal(candles=s_candles, indicators=s_ind, regime=s_regime, structure=s_struct, is_confirmed=True)

    plan_sell = TradeDecisionEngine.calculate_decision(
        candles=s_candles,
        indicators=s_ind,
        regime=s_regime,
        structure=s_struct,
        signal=s_signal,
        quality=quality,
        strategy_context_id="PHASE5_BASELINE",
        is_confirmed=True,
    )
    print(f"Candle Timestamp: {s_candles[-1].timestamp} ({s_candles[-1].close})")
    print(f"Signal: {s_signal.direction} (Score: {s_signal.score})")
    print(f"Decision: {plan_sell.decision}")
    print(f"State: {plan_sell.state}")
    print(f"Alignment Score: {plan_sell.decision_alignment_score}")
    if plan_sell.entry:
        print(f"Planned Entry: {plan_sell.entry.planned_entry_price} (Zone: {plan_sell.entry.entry_zone_low} - {plan_sell.entry.entry_zone_high})")
        print(f"Stop Loss: {plan_sell.stop_loss.price} (Risk: ${plan_sell.stop_loss.distance:.2f}, {plan_sell.stop_loss.distance_atr:.2f} ATR)")
        print(f"TP1: {plan_sell.take_profits.tp1.adjusted_target} (RR: {plan_sell.take_profits.tp1.actual_rr_after_adjustment:.2f}R)")
        print(f"TP2: {plan_sell.take_profits.tp2.adjusted_target} (RR: {plan_sell.take_profits.tp2.actual_rr_after_adjustment:.2f}R)")
        print(f"TP3: {plan_sell.take_profits.tp3.adjusted_target} (RR: {plan_sell.take_profits.tp3.actual_rr_after_adjustment:.2f}R)")
    else:
        print(f"Reasons for NO_TRADE: {plan_sell.reasons_for_no_trade}")

if __name__ == "__main__":
    main()
