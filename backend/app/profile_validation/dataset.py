"""
Dataset helper for multi-timeframe profile backtesting.
"""

from typing import Dict, List
from app.data.schema import Candle, CandleStateEnum


def build_synthetic_multi_tf_dataset(
    base_price: float = 65000.0,
    primary_minutes: int = 1,
    primary_count: int = 300,
    start_ts: int = 1700000000000,
) -> Dict[str, List[Candle]]:
    """Generates synthetic causally aligned multi-timeframe candle datasets."""
    prim_candles = []
    p = base_price
    t = start_ts
    interval_ms = primary_minutes * 60 * 1000

    for i in range(primary_count):
        delta = ((i % 5) - 2) * 15.0 + ((i % 11) - 5) * 5.0
        p = max(1000.0, p + delta)
        prim_candles.append(
            Candle(
                timestamp=t,
                open=p - 10.0,
                high=p + 25.0,
                low=p - 25.0,
                close=p,
                volume=120.0 + (i % 7) * 20.0,
                close_time=t + interval_ms - 1,
                is_closed=True,
                state=CandleStateEnum.CLOSED,
            )
        )
        t += interval_ms

    # Aggregate to 5m, 15m, 1h, 4h, 1d
    def aggregate_candles(source: List[Candle], tf_minutes: int) -> List[Candle]:
        tf_ms = tf_minutes * 60 * 1000
        aggregated = []
        curr_bucket = None

        for c in source:
            bucket_start = (c.timestamp // tf_ms) * tf_ms
            if not curr_bucket or curr_bucket["timestamp"] != bucket_start:
                if curr_bucket:
                    aggregated.append(
                        Candle(
                            timestamp=curr_bucket["timestamp"],
                            open=curr_bucket["open"],
                            high=curr_bucket["high"],
                            low=curr_bucket["low"],
                            close=curr_bucket["close"],
                            volume=curr_bucket["volume"],
                            close_time=curr_bucket["timestamp"] + tf_ms - 1,
                            is_closed=True,
                            state=CandleStateEnum.CLOSED,
                        )
                    )
                curr_bucket = {
                    "timestamp": bucket_start,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
            else:
                curr_bucket["high"] = max(curr_bucket["high"], c.high)
                curr_bucket["low"] = min(curr_bucket["low"], c.low)
                curr_bucket["close"] = c.close
                curr_bucket["volume"] += c.volume

        if curr_bucket:
            aggregated.append(
                Candle(
                    timestamp=curr_bucket["timestamp"],
                    open=curr_bucket["open"],
                    high=curr_bucket["high"],
                    low=curr_bucket["low"],
                    close=curr_bucket["close"],
                    volume=curr_bucket["volume"],
                    close_time=curr_bucket["timestamp"] + tf_ms - 1,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
        return aggregated

    dataset = {
        "1m": prim_candles,
        "5m": aggregate_candles(prim_candles, 5),
        "15m": aggregate_candles(prim_candles, 15),
        "1h": aggregate_candles(prim_candles, 60),
        "4h": aggregate_candles(prim_candles, 240),
        "1d": aggregate_candles(prim_candles, 1440),
    }
    return dataset
