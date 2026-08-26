import pytest
from app.data.schema import Candle, CandleStateEnum, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.models import MarketRegimeSnapshot, DirectionEnum, OverallRegimeEnum, VolatilityStateEnum
from app.structure.models import MarketStructureSnapshot, SupportResistanceZone, ZoneTypeEnum, ZoneStatusEnum, ZoneStrengthEnum
from app.structure.engine import MarketStructureEngine
from app.signals.evidence import EvidenceExtractor
from app.signals.conflicts import ConflictDetector
from app.signals.config import default_signal_config
from app.signals.models import ConflictSeverityEnum


def create_sample_candles(count: int = 100, trend: str = "bullish"):
    candles = []
    base_price = 50000.0
    for i in range(count):
        close = base_price + (i * 50.0 if trend == "bullish" else -i * 50.0)
        c = Candle(
            timestamp=1700000000000 + i * 900000,
            open=close - 10.0,
            high=close + 20.0,
            low=close - 20.0,
            close=close,
            volume=100.0,
            close_time=1700000000000 + i * 900000 + 899999,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        candles.append(c)
    return candles


def test_trend_structure_opposition_conflict():
    candles = create_sample_candles(100, trend="bullish")
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    regime = MarketRegimeSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=candles[-1].timestamp,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        direction=DirectionEnum.BULLISH,
        trend_strength="STRONG",
        volatility_state=VolatilityStateEnum.NORMAL,
        momentum_state="POSITIVE",
        volume_state="NORMAL",
        structure_state="BEARISH",
        overall_regime=OverallRegimeEnum.TRENDING_BULLISH,
        evidence_strength=80.0,
        evidence=[],
        contradictions=[],
    )
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)
    struct.structure_direction = "BEARISH"  # Simulating opposing bearish structure

    trend_group = EvidenceExtractor.extract_trend_evidence(ind, candles, default_signal_config)
    mom_group = EvidenceExtractor.extract_momentum_evidence(ind, regime, default_signal_config)
    struct_group = EvidenceExtractor.extract_structure_evidence(struct, default_signal_config)
    vol_group = EvidenceExtractor.extract_volume_evidence(ind, struct, default_signal_config)

    conflicts = ConflictDetector.detect_conflicts(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        trend_group=trend_group,
        momentum_group=mom_group,
        structure_group=struct_group,
        volume_group=vol_group,
        config=default_signal_config,
    )

    opp_conflict = next((c for c in conflicts if "OPPOSITION" in c.conflict_id), None)
    assert opp_conflict is not None
    assert opp_conflict.severity == ConflictSeverityEnum.HIGH
    assert opp_conflict.applied_penalty == 25.0


def test_sr_resistance_proximity_penalty():
    candles = create_sample_candles(100, trend="bullish")
    last_close = candles[-1].close
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    regime = MarketRegimeSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=candles[-1].timestamp,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        direction=DirectionEnum.BULLISH,
        trend_strength="STRONG",
        volatility_state=VolatilityStateEnum.NORMAL,
        momentum_state="POSITIVE",
        volume_state="NORMAL",
        structure_state="BULLISH",
        overall_regime=OverallRegimeEnum.TRENDING_BULLISH,
        evidence_strength=80.0,
        evidence=[],
        contradictions=[],
    )
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)

    # Place a strong resistance zone immediately above current close (within 0.1 ATR)
    atr = ind.volatility.atr or 100.0
    res_zone = SupportResistanceZone(
        zone_id="RES_TEST",
        zone_type=ZoneTypeEnum.RESISTANCE,
        price_low=last_close + (atr * 0.1),
        price_high=last_close + (atr * 0.2),
        price_center=last_close + (atr * 0.15),
        touch_count=3,
        strength=ZoneStrengthEnum.STRONG,
        status=ZoneStatusEnum.ACTIVE,
        created_timestamp=1700000000000,
        last_touch_timestamp=1700000000000,
    )
    struct.resistance_zones.append(res_zone)

    trend_group = EvidenceExtractor.extract_trend_evidence(ind, candles, default_signal_config)
    mom_group = EvidenceExtractor.extract_momentum_evidence(ind, regime, default_signal_config)
    struct_group = EvidenceExtractor.extract_structure_evidence(struct, default_signal_config)
    vol_group = EvidenceExtractor.extract_volume_evidence(ind, struct, default_signal_config)

    conflicts = ConflictDetector.detect_conflicts(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        trend_group=trend_group,
        momentum_group=mom_group,
        structure_group=struct_group,
        volume_group=vol_group,
        config=default_signal_config,
    )

    sr_conflict = next((c for c in conflicts if c.conflict_id == "SR_RESISTANCE_PROXIMITY"), None)
    assert sr_conflict is not None
    assert sr_conflict.severity == ConflictSeverityEnum.HIGH


def test_critical_data_quality_conflict():
    candles = create_sample_candles(100, trend="bullish")
    ind = IndicatorEngine.calculate_snapshot(candles, symbol="BTCUSDT", timeframe="15m", is_confirmed=True)
    regime = MarketRegimeSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        timestamp=candles[-1].timestamp,
        candle_state=CandleStateEnum.CLOSED,
        is_confirmed=True,
        direction=DirectionEnum.BULLISH,
        trend_strength="STRONG",
        volatility_state=VolatilityStateEnum.NORMAL,
        momentum_state="POSITIVE",
        volume_state="NORMAL",
        structure_state="BULLISH",
        overall_regime=OverallRegimeEnum.TRENDING_BULLISH,
        evidence_strength=80.0,
        evidence=[],
        contradictions=[],
    )
    struct = MarketStructureEngine.evaluate(candles, indicators=ind, is_confirmed=True)

    invalid_quality = MarketDataQuality(
        symbol="BTCUSDT",
        timeframe="15m",
        status=QualityStatusEnum.INVALID,
        total_candles=100,
        valid_candles=0,
        gap_count=5,
        duplicate_count=0,
        out_of_order_count=0,
        is_stale=True,
        details=["Synthetic corruption"],
    )

    trend_group = EvidenceExtractor.extract_trend_evidence(ind, candles, default_signal_config)
    mom_group = EvidenceExtractor.extract_momentum_evidence(ind, regime, default_signal_config)
    struct_group = EvidenceExtractor.extract_structure_evidence(struct, default_signal_config)
    vol_group = EvidenceExtractor.extract_volume_evidence(ind, struct, default_signal_config)

    conflicts = ConflictDetector.detect_conflicts(
        candles=candles,
        indicators=ind,
        regime=regime,
        structure=struct,
        trend_group=trend_group,
        momentum_group=mom_group,
        structure_group=struct_group,
        volume_group=vol_group,
        quality=invalid_quality,
        config=default_signal_config,
    )

    crit = next((c for c in conflicts if c.severity == ConflictSeverityEnum.CRITICAL), None)
    assert crit is not None
    assert crit.conflict_id == "DATA_QUALITY_CRITICAL"
