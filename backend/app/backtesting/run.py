"""
Command-Line Interface (CLI) for running backtest validation runs.
Usage:
    python -m app.backtesting.run --symbol BTCUSDT --timeframe 15m --candles 1000
    python -m app.backtesting.run --dataset data/processed/BTCUSDT_15m_...json
"""

import argparse
import sys
import os
import time
from datetime import datetime, timezone

from app.backtesting.config import BacktestConfig, CostModelConfig
from app.backtesting.dataset import DatasetManager
from app.backtesting.downloader import BinanceHistoricalDownloader
from app.backtesting.engine import BacktestEngine
from app.backtesting.reports import ReportGenerator
from app.core.logging import logger


def parse_args():
    parser = argparse.ArgumentParser(description="Crypto AI Trading Intelligence — Backtesting CLI")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading pair symbol (default: BTCUSDT)")
    parser.add_argument("--timeframe", type=str, default="15m", help="Candle timeframe (default: 15m)")
    parser.add_argument("--candles", type=int, default=1000, help="Number of candles to download/test (default: 1000)")
    parser.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--dataset", type=str, default=None, help="Path to pre-existing processed dataset JSON")
    parser.add_argument("--warmup", type=int, default=50, help="Warmup bars count (default: 50)")
    parser.add_argument("--fee-bps", type=float, default=0.0, help="Fee in basis points (default: 0.0)")
    parser.add_argument("--slippage-bps", type=float, default=0.0, help="Slippage in basis points (default: 0.0)")
    return parser.parse_args()


def main():
    args = parse_args()

    symbol = args.symbol.upper()
    timeframe = args.timeframe

    start_ts = None
    if args.start:
        dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ts = int(dt.timestamp() * 1000)

    end_ts = None
    if args.end:
        dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_ts = int(dt.timestamp() * 1000)

    dm = DatasetManager()

    if args.dataset:
        print(f"Loading processed dataset from {args.dataset}...")
        candles, metadata = dm.load_processed_dataset(args.dataset)
    else:
        print(f"Acquiring historical market data for {symbol}@{timeframe} ({args.candles} candles)...")
        dl = BinanceHistoricalDownloader()
        raw_path = dl.download_klines(
            symbol=symbol,
            timeframe=timeframe,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            max_candles=args.candles,
        )
        candles, metadata = dm.load_from_raw_file(raw_path)
        processed_path = dm.save_processed_dataset(candles, metadata)
        print(f"Saved processed dataset: {processed_path}")

    # Build Config
    cost_cfg = CostModelConfig(
        enabled=(args.fee_bps > 0 or args.slippage_bps > 0),
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
    )

    config = BacktestConfig(
        symbol=symbol,
        timeframe=timeframe,
        warmup_bars=args.warmup,
        cost_model=cost_cfg,
    )

    print(f"\nExecuting causal sequential backtest on {len(candles)} candles...")
    t0 = time.time()
    run = BacktestEngine.run(candles, config=config, dataset_metadata=metadata)
    elapsed = time.time() - t0

    print(f"Backtest execution completed in {elapsed:.2f} seconds.")
    print("\n" + ReportGenerator.format_cli_summary(run))


if __name__ == "__main__":
    main()
