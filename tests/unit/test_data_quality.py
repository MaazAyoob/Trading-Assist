import pytest
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum
from app.data.quality import MarketDataQualityValidator


def create_candle(ts: int, o: float, h: float, l: float, c: float, v: float, state=CandleStateEnum.CLOSED) -> Candle:
    return Candle(
        timestamp=ts,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        close_time=ts + 899999,
        is_closed=(state == CandleStateEnum.CLOSED),
        state=state,
    )


def test_validate_single_candle_valid():
    c = create_candle(1700000000000, 50000.0, 51000.0, 49000.0, 50500.0, 10.0)
    is_valid, errs = MarketDataQualityValidator.validate_candle(c)
    assert is_valid is True
    assert len(errs) == 0


def test_validate_single_candle_invalid_ohlc():
    # high < open
    c1 = create_candle(1700000000000, 50000.0, 49000.0, 48000.0, 48500.0, 10.0)
    is_valid, errs = MarketDataQualityValidator.validate_candle(c1)
    assert is_valid is False
    assert any("High" in e for e in errs)

    # low > close
    c2 = create_candle(1700000000000, 50000.0, 51000.0, 50200.0, 50100.0, 10.0)
    is_valid, errs = MarketDataQualityValidator.validate_candle(c2)
    assert is_valid is False
    assert any("Low" in e for e in errs)

    # negative price
    c3 = create_candle(1700000000000, -100.0, 51000.0, 49000.0, 50500.0, 10.0)
    is_valid, errs = MarketDataQualityValidator.validate_candle(c3)
    assert is_valid is False

    # negative volume
    c4 = create_candle(1700000000000, 50000.0, 51000.0, 49000.0, 50500.0, -5.0)
    is_valid, errs = MarketDataQualityValidator.validate_candle(c4)
    assert is_valid is False


def test_validate_dataset_healthy_sequence():
    base_ts = 1700000000000
    candles = [
        create_candle(base_ts + i * 900000, 50000.0 + i, 50100.0 + i, 49900.0 + i, 50050.0 + i, 10.0)
        for i in range(10)
    ]
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=5, now_ms=base_ts + 9 * 900000 + 1000
    )
    assert len(clean) == 10
    assert quality.status == QualityStatusEnum.HEALTHY
    assert quality.duplicate_count == 0
    assert quality.gap_count == 0
    assert quality.invalid_count == 0


def test_validate_dataset_duplicates_rejection():
    base_ts = 1700000000000
    candles = [
        create_candle(base_ts, 50000.0, 50100.0, 49900.0, 50050.0, 10.0),
        create_candle(base_ts, 50000.0, 50100.0, 49900.0, 50050.0, 10.0),  # duplicate
        create_candle(base_ts + 900000, 50050.0, 50200.0, 50000.0, 50150.0, 12.0),
    ]
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=1, now_ms=base_ts + 900000 + 1000
    )
    assert len(clean) == 2
    assert quality.duplicate_count == 1
    assert quality.status == QualityStatusEnum.WARNING


def test_validate_dataset_out_of_order_rejection():
    base_ts = 1700000000000
    candles = [
        create_candle(base_ts + 900000, 50000.0, 50100.0, 49900.0, 50050.0, 10.0),
        create_candle(base_ts, 50050.0, 50200.0, 50000.0, 50150.0, 12.0),  # out of order
    ]
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=1, now_ms=base_ts + 900000 + 1000
    )
    assert len(clean) == 1
    assert quality.invalid_count == 1
    assert quality.status == QualityStatusEnum.INVALID


def test_validate_dataset_gap_detection_without_fabrication():
    base_ts = 1700000000000
    candles = [
        create_candle(base_ts, 50000.0, 50100.0, 49900.0, 50050.0, 10.0),
        # missing 15m candle (base_ts + 900000)
        create_candle(base_ts + 1800000, 50050.0, 50200.0, 50000.0, 50150.0, 12.0),
    ]
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=1, now_ms=base_ts + 1800000 + 1000
    )
    # Output length MUST remain 2 (no fabricated candles inserted)
    assert len(clean) == 2
    assert quality.gap_count == 1
    assert quality.status == QualityStatusEnum.WARNING


def test_validate_dataset_insufficient_data():
    base_ts = 1700000000000
    candles = [create_candle(base_ts, 50000.0, 50100.0, 49900.0, 50050.0, 10.0)]
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=10, now_ms=base_ts + 1000
    )
    assert quality.status == QualityStatusEnum.INSUFFICIENT_DATA


def test_validate_dataset_stale_detection():
    base_ts = 1700000000000
    candles = [create_candle(base_ts, 50000.0, 50100.0, 49900.0, 50050.0, 10.0)]
    # Now time is 2 hours later (7200000ms) on a 15m candle (900000ms)
    clean, quality = MarketDataQualityValidator.validate_dataset(
        candles, symbol="BTCUSDT", timeframe="15m", min_required=1, now_ms=base_ts + 7200000
    )
    assert quality.stale is True
    assert quality.status == QualityStatusEnum.WARNING
