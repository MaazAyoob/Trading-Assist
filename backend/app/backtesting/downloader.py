"""
Safe, rate-limited, paginated historical market data downloader using Binance public REST API.
Raw downloads are stored immutably without modification in data/raw/.
"""

import os
import json
import time
import httpx
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.core.timeframes import SUPPORTED_TIMEFRAMES, get_timeframe_ms


class BinanceHistoricalDownloader:
    """
    Downloads historical OHLCV klines from Binance public endpoint.
    Handles pagination, rate limiting, retries, resume/cache detection, and raw data immutability.
    """

    BASE_URL = "https://api.binance.com/api/v3/klines"
    MAX_LIMIT = 1000

    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_data_dir = raw_data_dir
        os.makedirs(self.raw_data_dir, exist_ok=True)

    def download_klines(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "15m",
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        max_candles: Optional[int] = None,
        force_redownload: bool = False,
    ) -> str:
        """
        Paginates and downloads klines, saving the exact raw response to data/raw/.
        Returns the absolute filepath of the saved raw JSON file.
        """
        symbol = symbol.upper()
        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {SUPPORTED_TIMEFRAMES}")

        interval_ms = get_timeframe_ms(timeframe)
        now_ms = int(time.time() * 1000)

        if end_timestamp is None:
            end_timestamp = now_ms

        if start_timestamp is None:
            count = max_candles or 500
            start_timestamp = end_timestamp - (count * interval_ms)

        filename = f"{symbol}_{timeframe}_{start_timestamp}_{end_timestamp}.json"
        raw_filepath = os.path.join(self.raw_data_dir, filename)

        # Check existing cache
        if not force_redownload and os.path.exists(raw_filepath):
            try:
                with open(raw_filepath, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("raw_candle_count", 0) > 0:
                    logger.info(
                        f"Found existing cached raw dataset for {symbol}@{timeframe} ({cached['raw_candle_count']} bars) at {raw_filepath}"
                    )
                    return os.path.abspath(raw_filepath)
            except Exception as e:
                logger.warning(f"Failed to read existing raw file {raw_filepath}: {e}. Redownloading...")

        logger.info(
            f"Starting historical paginated download for {symbol}@{timeframe} from {start_timestamp} to {end_timestamp}"
        )

        all_raw_klines: List[List[Any]] = []
        seen_open_times = set()
        curr_start = start_timestamp
        client = httpx.Client(timeout=30.0)

        total_expected_candles = max(1, (end_timestamp - start_timestamp) // interval_ms)
        if max_candles:
            total_expected_candles = min(total_expected_candles, max_candles)

        try:
            while curr_start < end_timestamp:
                params = {
                    "symbol": symbol,
                    "interval": timeframe,
                    "startTime": curr_start,
                    "endTime": end_timestamp,
                    "limit": self.MAX_LIMIT,
                }

                # Robust retry loop with exponential backoff
                retries = 5
                batch = None
                for attempt in range(retries):
                    try:
                        resp = client.get(self.BASE_URL, params=params)
                        if resp.status_code in (429, 418):
                            backoff = 5.0 * (attempt + 1)
                            logger.warning(f"Binance rate limit hit (HTTP {resp.status_code}). Backing off {backoff:.1f}s...")
                            time.sleep(backoff)
                            continue
                        resp.raise_for_status()
                        batch = resp.json()
                        break
                    except Exception as e:
                        if attempt == retries - 1:
                            logger.error(f"Failed to download kline batch starting at {curr_start}: {e}")
                            raise e
                        backoff = 1.0 * (2 ** attempt)
                        logger.warning(f"Download attempt {attempt+1} failed: {e}. Retrying in {backoff:.1f}s...")
                        time.sleep(backoff)

                if not batch or len(batch) == 0:
                    break

                # Deduplicate and append
                new_candles = 0
                for k in batch:
                    open_time = int(k[0])
                    if open_time not in seen_open_times:
                        seen_open_times.add(open_time)
                        all_raw_klines.append(k)
                        new_candles += 1

                last_open_time = int(batch[-1][0])
                if last_open_time <= curr_start:
                    # Prevent infinite loop if timestamp didn't advance
                    break

                curr_start = last_open_time + interval_ms

                if max_candles and len(all_raw_klines) >= max_candles:
                    all_raw_klines = all_raw_klines[:max_candles]
                    break

                # Progress reporting
                if len(all_raw_klines) % 5000 < self.MAX_LIMIT:
                    pct = min(100.0, (len(all_raw_klines) / total_expected_candles) * 100.0)
                    logger.info(f"Downloaded {len(all_raw_klines)} / ~{total_expected_candles} candles ({pct:.1f}%)...")

                # Respect Binance weight limits
                time.sleep(0.05)

        finally:
            client.close()

        # Sort raw klines strictly chronologically
        all_raw_klines.sort(key=lambda k: int(k[0]))

        # Save raw JSON file immutably
        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "download_timestamp": int(time.time() * 1000),
            "raw_candle_count": len(all_raw_klines),
            "klines": all_raw_klines,
        }

        with open(raw_filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(
            f"Successfully downloaded {len(all_raw_klines)} raw klines for {symbol}@{timeframe} -> {raw_filepath}"
        )
        return os.path.abspath(raw_filepath)
