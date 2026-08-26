import time
from typing import List, Tuple, Optional
from app.core.timeframes import get_timeframe_ms
from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum


class MarketDataQualityValidator:
    """
    Dedicated quantitative validator for OHLCV candlestick data streams and historical batches.
    Validates:
    - OHLC geometric consistency (high >= max(open, close), low <= min(open, close))
    - Positive prices and non-negative volume
    - Timestamp validity and strict chronological ordering
    - Duplicate detection (symbol + timeframe + timestamp)
    - Interval gaps based on centralized timeframe mapping
    - Data staleness relative to current UTC time
    - Does NOT mutate input datasets or fabricate missing candles
    """

    @staticmethod
    def validate_candle(candle: Candle) -> Tuple[bool, List[str]]:
        """Validate a single candle's internal numeric consistency."""
        errors: List[str] = []

        if candle.open <= 0:
            errors.append(f"Invalid open price: {candle.open} <= 0")
        if candle.high <= 0:
            errors.append(f"Invalid high price: {candle.high} <= 0")
        if candle.low <= 0:
            errors.append(f"Invalid low price: {candle.low} <= 0")
        if candle.close <= 0:
            errors.append(f"Invalid close price: {candle.close} <= 0")
        if candle.volume < 0:
            errors.append(f"Invalid volume: {candle.volume} < 0")

        if candle.high < max(candle.open, candle.close):
            errors.append(
                f"High {candle.high} is less than max(open={candle.open}, close={candle.close})"
            )
        if candle.low > min(candle.open, candle.close):
            errors.append(
                f"Low {candle.low} is greater than min(open={candle.open}, close={candle.close})"
            )
        if candle.timestamp <= 0:
            errors.append(f"Invalid timestamp: {candle.timestamp} <= 0")

        return len(errors) == 0, errors

    @classmethod
    def validate_dataset(
        cls,
        candles: List[Candle],
        symbol: str,
        timeframe: str,
        min_required: int = 1,
        now_ms: Optional[int] = None,
    ) -> Tuple[List[Candle], MarketDataQuality]:
        """
        Validate a batch of candles without mutating the input list.
        Returns a tuple of (clean_candles, data_quality_report).
        """
        messages: List[str] = []
        clean_candles: List[Candle] = []
        seen_timestamps = set()

        duplicate_count = 0
        invalid_count = 0
        gap_count = 0
        is_stale = False

        if now_ms is None:
            now_ms = int(time.time() * 1000)

        try:
            expected_interval_ms = get_timeframe_ms(timeframe)
        except ValueError as err:
            return [], MarketDataQuality(
                symbol=symbol.upper(),
                timeframe=timeframe,
                status=QualityStatusEnum.INVALID,
                latest_timestamp=None,
                candle_count=0,
                duplicate_count=0,
                gap_count=0,
                invalid_count=len(candles),
                stale=False,
                validation_messages=[str(err)],
            )

        if not candles or len(candles) == 0:
            return [], MarketDataQuality(
                symbol=symbol.upper(),
                timeframe=timeframe,
                status=QualityStatusEnum.INSUFFICIENT_DATA,
                latest_timestamp=None,
                candle_count=0,
                duplicate_count=0,
                gap_count=0,
                invalid_count=0,
                stale=False,
                validation_messages=["Dataset is empty"],
            )

        gap_records = []
        prev_timestamp: Optional[int] = None

        for idx, candle in enumerate(candles):
            # 1. Structural OHLC validation
            is_valid, errs = cls.validate_candle(candle)
            if not is_valid:
                invalid_count += 1
                messages.append(f"Candle index {idx} (ts {candle.timestamp}) invalid: {'; '.join(errs)}")
                continue

            # 2. Duplicate detection
            if candle.timestamp in seen_timestamps:
                duplicate_count += 1
                messages.append(f"Duplicate timestamp detected at index {idx}: {candle.timestamp}")
                continue

            # 3. Ordering validation
            if prev_timestamp is not None:
                if candle.timestamp <= prev_timestamp:
                    invalid_count += 1
                    messages.append(
                        f"Out-of-order timestamp at index {idx}: {candle.timestamp} <= previous {prev_timestamp}"
                    )
                    continue

                # 4. Gap detection (gap exists if delta > 1.5 * interval)
                delta_ms = candle.timestamp - prev_timestamp
                if delta_ms > int(expected_interval_ms * 1.5):
                    missing_intervals = round(delta_ms / expected_interval_ms) - 1
                    gap_count += max(1, missing_intervals)
                    gap_records.append({
                        "gap_start": prev_timestamp,
                        "gap_end": candle.timestamp,
                        "missing_candle_count": max(1, missing_intervals),
                    })
                    messages.append(
                        f"Gap detected between {prev_timestamp} and {candle.timestamp} (~{missing_intervals} missing candles)"
                    )

            seen_timestamps.add(candle.timestamp)
            prev_timestamp = candle.timestamp
            clean_candles.append(candle)

        # 5. Stale data detection
        latest_ts = clean_candles[-1].timestamp if clean_candles else None
        if latest_ts is not None:
            # Stale threshold: if latest candle is older than 2.5 intervals + 60s network margin
            stale_threshold_ms = int(expected_interval_ms * 2.5) + 60000
            if (now_ms - latest_ts) > stale_threshold_ms:
                is_stale = True
                messages.append(
                    f"Market data appears STALE: latest candle {latest_ts} is older than threshold ({now_ms - latest_ts}ms lag)"
                )

        # 6. Overall Quality Status
        if len(clean_candles) < min_required:
            status = QualityStatusEnum.INSUFFICIENT_DATA
            messages.append(
                f"Insufficient candles: {len(clean_candles)} valid candles < {min_required} required"
            )
        elif invalid_count > 0:
            status = QualityStatusEnum.INVALID
        elif gap_count > 0 or duplicate_count > 0 or is_stale:
            status = QualityStatusEnum.WARNING
        else:
            status = QualityStatusEnum.HEALTHY

        quality = MarketDataQuality(
            symbol=symbol.upper(),
            timeframe=timeframe,
            status=status,
            latest_timestamp=latest_ts,
            candle_count=len(clean_candles),
            duplicate_count=duplicate_count,
            gap_count=gap_count,
            invalid_count=invalid_count,
            gaps=gap_records,
            stale=is_stale,
            validation_messages=messages,
        )

        return clean_candles, quality
