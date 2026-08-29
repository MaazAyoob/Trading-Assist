"""
Run Phase 13D Calibration & Timing Diagnostic on local 1000 BTCUSDT candles dataset.
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend"))

from app.data.binance import BinanceMarketDataProvider
from app.scalp_v2.diagnostics import ScalpV2DiagnosticEngine


async def main():
    provider = BinanceMarketDataProvider()
    print("Fetching 1m, 5m, 15m candles...", flush=True)
    candles_1m = await provider.get_historical_klines("BTCUSDT", "1m", limit=1000)
    try:
        candles_5m = await provider.get_historical_klines("BTCUSDT", "5m", limit=200)
    except Exception:
        candles_5m = []

    try:
        candles_15m = await provider.get_historical_klines("BTCUSDT", "15m", limit=100)
    except Exception:
        candles_15m = []

    print(f"Fetched 1m={len(candles_1m)}, 5m={len(candles_5m)}, 15m={len(candles_15m)}", flush=True)

    t0 = time.time()
    report = ScalpV2DiagnosticEngine.run_diagnostics(
        candles_1m=candles_1m,
        candles_5m=candles_5m,
        candles_15m=candles_15m,
        symbol="BTCUSDT",
    )
    t1 = time.time()

    print(f"DIAGNOSTIC TIME: {t1 - t0:.3f}s")
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
