"""
Live / Historical 1-Minute BTCUSDT Candle Frequency Diagnostic Check for SCALP_STRATEGY_V2.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.data.binance import BinanceMarketDataProvider
from app.scalp_v2.engine import ScalpV2StrategyEngine
from app.scalp_v2.models import ScalpV2Direction, ScalpV2SetupType


async def main():
    provider = BinanceMarketDataProvider()
    symbol = "BTCUSDT"
    timeframe = "1m"

    try:
        print("Fetching 1-minute BTCUSDT candles from market provider...", flush=True)
        candles_1m = await provider.get_historical_klines(symbol=symbol, timeframe=timeframe, limit=1000)
        print(f"Total 1m candles fetched: {len(candles_1m)}", flush=True)

        if not candles_1m or len(candles_1m) < 60:
            print("Insufficient candles. Aborting.", flush=True)
            return

        try:
            candles_5m = await provider.get_historical_klines(symbol=symbol, timeframe="5m", limit=200)
        except Exception:
            candles_5m = []

        # Reset engine state for clean sequential simulation
        ScalpV2StrategyEngine.reset_state()

        evaluated_count = 0
        buy_count = 0
        sell_count = 0
        watch_count = 0
        no_trade_count = 0

        continuation_count = 0
        pullback_count = 0
        breakout_count = 0

        scores = []
        abs_scores = []

        start_idx = 60
        total_steps = len(candles_1m) - start_idx
        print(f"Starting evaluation across {total_steps} closed candles...", flush=True)

        for i in range(start_idx, len(candles_1m) + 1):
            window_1m = candles_1m[max(0, i - 150):i]
            curr_ts = window_1m[-1].timestamp
            
            # Context 5m up to current timestamp
            window_5m = [c for c in candles_5m if c.timestamp <= curr_ts]
            if len(window_5m) > 100:
                window_5m = window_5m[-100:]

            sig = ScalpV2StrategyEngine.evaluate(
                candles_1m=window_1m,
                candles_5m=window_5m if window_5m else None,
                symbol=symbol,
                is_preview=False,
            )

            evaluated_count += 1
            scores.append(sig.score)
            abs_scores.append(sig.alignment_score)

            if sig.direction == ScalpV2Direction.BUY:
                buy_count += 1
            elif sig.direction == ScalpV2Direction.SELL:
                sell_count += 1
            elif sig.direction == ScalpV2Direction.WATCH:
                watch_count += 1
            else:
                no_trade_count += 1

            if sig.direction in (ScalpV2Direction.BUY, ScalpV2Direction.SELL):
                if sig.setup_type == ScalpV2SetupType.TREND_CONTINUATION:
                    continuation_count += 1
                elif sig.setup_type == ScalpV2SetupType.PULLBACK:
                    pullback_count += 1
                elif sig.setup_type == ScalpV2SetupType.MOMENTUM_BREAKOUT:
                    breakout_count += 1

        total_signals = buy_count + sell_count
        hours_evaluated = evaluated_count / 60.0

        signals_per_hour = total_signals / hours_evaluated if hours_evaluated > 0 else 0
        signals_per_4_hours = signals_per_hour * 4.0
        signals_per_24_hours = signals_per_hour * 24.0

        avg_abs_score = sum(abs_scores) / len(abs_scores) if abs_scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0

        print("\n" + "=" * 60, flush=True)
        print("SCALP_STRATEGY_V2 — FINAL LIVE SIGNAL-FREQUENCY CHECK RESULTS", flush=True)
        print("=" * 60, flush=True)
        print(f"- Total candles evaluated: {evaluated_count}", flush=True)
        print(f"- BUY signals generated: {buy_count}", flush=True)
        print(f"- SELL signals generated: {sell_count}", flush=True)
        print(f"- WATCH states: {watch_count}", flush=True)
        print(f"- NO_TRADE states: {no_trade_count}", flush=True)
        print(f"- Signals per hour: {signals_per_hour:.2f}", flush=True)
        print(f"- Signals per 4 hours: {signals_per_4_hours:.2f}", flush=True)
        print(f"- Signals per 24 hours: {signals_per_24_hours:.2f}", flush=True)
        print(f"- Continuation signals: {continuation_count}", flush=True)
        print(f"- Pullback signals: {pullback_count}", flush=True)
        print(f"- Breakout signals: {breakout_count}", flush=True)
        print(f"- Average absolute score: {avg_abs_score:.2f}", flush=True)
        print(f"- Minimum score observed: {min_score:.2f}", flush=True)
        print(f"- Maximum score observed: {max_score:.2f}", flush=True)
        print("=" * 60, flush=True)

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())
