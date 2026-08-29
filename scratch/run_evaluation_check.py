"""
Script to execute historical evaluation of SCALP_STRATEGY_V2 on local/live dataset.
Prints the 12 required items for the Phase 13C report.
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.data.binance import BinanceMarketDataProvider
from app.scalp_v2.evaluation import run_scalp_v2_historical_evaluation


async def main():
    provider = BinanceMarketDataProvider()
    print("Fetching 1m, 5m, 15m candles from provider...", flush=True)
    candles_1m = await provider.get_historical_klines("BTCUSDT", "1m", limit=1000)
    try:
        candles_5m = await provider.get_historical_klines("BTCUSDT", "5m", limit=200)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines("BTCUSDT", "15m", limit=100)
    except Exception:
        candles_15m = []

    print(f"Candles retrieved: 1m={len(candles_1m)}, 5m={len(candles_5m)}, 15m={len(candles_15m)}", flush=True)

    report = run_scalp_v2_historical_evaluation(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol="BTCUSDT",
    )

    print("\n" + "=" * 60)
    print("PHASE 13C — HISTORICAL SIGNAL QUALITY EVALUATION REPORT")
    print("=" * 60)
    print(f"1. Total candles: {report.dataset_candles}")
    print(f"2. Dataset duration: {report.dataset_duration_hours:.2f} hours ({report.candles_evaluated} evaluated)")
    print(f"3. V1 signals: {report.frequency_comparison.v1_signals} ({report.frequency_comparison.v1_signals_per_hour:.2f}/hour)")
    print(f"4. V2 signals: {report.frequency_comparison.v2_signals} ({report.frequency_comparison.v2_signals_per_hour:.2f}/hour)")
    print(f"5. V2 signals/hour: {report.frequency_comparison.v2_signals_per_hour:.2f}")
    print(f"6. BUY/SELL counts: {report.buy_signals} BUY, {report.sell_signals} SELL (WATCH: {report.watch_states}, NO_TRADE: {report.no_trade_states})")
    print("\n7. Setup distribution:")
    for s in report.setup_breakdown:
        print(f"   - {s.setup_type}: {s.signals} signals")

    print("\n8. TP1 hit rate by horizon:")
    print("   Horizon | Signals | TP1 Hits | SL Hits | Ambiguous | Historical TP1 Hit Rate")
    print("   " + "-" * 70)
    for h in report.horizon_analysis:
        print(f"   {h.horizon_candles:>2} candles | {h.signals:>7} | {h.tp1_hits:>8} | {h.sl_hits:>7} | {h.ambiguous:>9} | {h.historical_tp1_hit_rate:>20.2f}%")

    print("\n9. TP1 hit rate by score bucket (20-candle horizon):")
    print("   Score Bucket | Signals | BUY / SELL | TP1 Hits | SL Hits | Ambiguous | Historical TP1 Hit Rate")
    print("   " + "-" * 80)
    for b in report.score_breakdown:
        print(f"   {b.bucket_label:>12} | {b.signals:>7} | {b.buy_count:>3}B / {b.sell_count:>3}S | {b.tp1_hits:>8} | {b.sl_hits:>7} | {b.ambiguous:>9} | {b.historical_tp1_hit_rate:>20.2f}%")

    print("\n10. TP1 hit rate by setup (20-candle horizon):")
    print("   Setup Type           | Signals | TP1 Hits | SL Hits | Ambiguous | Historical TP1 Hit Rate")
    print("   " + "-" * 80)
    for s in report.setup_breakdown:
        print(f"   {s.setup_type:<20} | {s.signals:>7} | {s.tp1_hits:>8} | {s.sl_hits:>7} | {s.ambiguous:>9} | {s.historical_tp1_hit_rate:>20.2f}%")

    ref_h20 = next((h for h in report.horizon_analysis if h.horizon_candles == 20), None)
    sl_count_20 = ref_h20.sl_hits if ref_h20 else 0
    amb_count_20 = ref_h20.ambiguous if ref_h20 else 0

    print(f"\n11. SL count (20-candle horizon): {sl_count_20}")
    print(f"12. Ambiguous count (20-candle horizon): {amb_count_20}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
