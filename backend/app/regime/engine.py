from typing import List, Optional, Tuple
import numpy as np
from app.data.schema import Candle, CandleStateEnum
from app.indicators.base import IndicatorSnapshot
from app.regime.config import RegimeConfig, default_regime_config
from app.regime.models import (
    DirectionEnum,
    TrendStrengthEnum,
    VolatilityStateEnum,
    MomentumStateEnum,
    VolumeStateEnum,
    StructureStateEnum,
    OverallRegimeEnum,
    EvidenceCategoryEnum,
    EvidenceItem,
    MarketRegimeSnapshot,
)


class MarketRegimeEngine:
    """
    Deterministic quantitative market regime classifier.
    Interprets indicators and structural state into multi-dimensional market environment metrics.
    """

    @classmethod
    def classify(
        cls,
        candles: List[Candle],
        indicators: IndicatorSnapshot,
        structure_state: StructureStateEnum = StructureStateEnum.UNKNOWN,
        is_confirmed: bool = True,
        config: Optional[RegimeConfig] = None,
    ) -> MarketRegimeSnapshot:
        cfg = config or default_regime_config
        symbol = indicators.symbol
        timeframe = indicators.timeframe
        ts = indicators.timestamp

        evidence: List[EvidenceItem] = []
        contradictions: List[EvidenceItem] = []

        trend = indicators.trend
        mom = indicators.momentum
        vol = indicators.volatility
        volume = indicators.volume

        # ----------------------------------------------------
        # 1. Trend & Direction Classification
        # ----------------------------------------------------
        bull_trend_votes = 0
        bear_trend_votes = 0

        # Group 1A: EMA Alignment
        if trend.ema_9 is not None and trend.ema_21 is not None and trend.ema_50 is not None:
            if trend.ema_9 > trend.ema_21 > trend.ema_50:
                bull_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="EMA Alignment: Stacked Bullish (9 > 21 > 50)",
                        metric_value=f"EMA9: {trend.ema_9:.2f} > EMA21: {trend.ema_21:.2f} > EMA50: {trend.ema_50:.2f}",
                    )
                )
            elif trend.ema_9 < trend.ema_21 < trend.ema_50:
                bear_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="EMA Alignment: Stacked Bearish (9 < 21 < 50)",
                        metric_value=f"EMA9: {trend.ema_9:.2f} < EMA21: {trend.ema_21:.2f} < EMA50: {trend.ema_50:.2f}",
                    )
                )

        # Group 1B: Supertrend Direction
        if trend.supertrend_direction is not None:
            if trend.supertrend_direction == 1:
                bull_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="Supertrend: Bullish boundary active",
                        metric_value=f"Level: {trend.supertrend}",
                    )
                )
            elif trend.supertrend_direction == -1:
                bear_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="Supertrend: Bearish boundary active",
                        metric_value=f"Level: {trend.supertrend}",
                    )
                )

        # Group 1C: Directional Movement (+DI vs -DI)
        if trend.plus_di is not None and trend.minus_di is not None:
            if trend.plus_di > trend.minus_di:
                bull_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="Directional Movement: +DI dominant over -DI",
                        metric_value=f"+DI: {trend.plus_di:.1f} vs -DI: {trend.minus_di:.1f}",
                    )
                )
            elif trend.minus_di > trend.plus_di:
                bear_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="Directional Movement: -DI dominant over +DI",
                        metric_value=f"-DI: {trend.minus_di:.1f} vs +DI: {trend.plus_di:.1f}",
                    )
                )

        # Group 1D: Rolling VWAP Position
        last_close = candles[-1].close if candles else None
        if last_close is not None and trend.vwap is not None:
            if last_close > trend.vwap:
                bull_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="VWAP Position: Price above 24h Rolling VWAP",
                        metric_value=f"Close: {last_close:.2f} > VWAP: {trend.vwap:.2f}",
                    )
                )
            else:
                bear_trend_votes += 1
                evidence.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.TREND,
                        description="VWAP Position: Price below 24h Rolling VWAP",
                        metric_value=f"Close: {last_close:.2f} < VWAP: {trend.vwap:.2f}",
                    )
                )

        # Determine Direction
        adx_val = trend.adx or 0.0
        if adx_val < cfg.ADX_TREND_THRESHOLD:
            # Low ADX suppresses strong directional label into RANGE
            direction = DirectionEnum.RANGE
            evidence.append(
                EvidenceItem(
                    category=EvidenceCategoryEnum.TREND,
                    description="Trend State: Indecisive/Ranging market structure (ADX < Threshold)",
                    metric_value=f"ADX: {adx_val:.1f} < {cfg.ADX_TREND_THRESHOLD}",
                )
            )
        elif bull_trend_votes >= 3 and bear_trend_votes <= 1:
            direction = DirectionEnum.BULLISH
        elif bear_trend_votes >= 3 and bull_trend_votes <= 1:
            direction = DirectionEnum.BEARISH
        else:
            direction = DirectionEnum.UNCERTAIN

        # ----------------------------------------------------
        # 2. Trend Strength Classification
        # ----------------------------------------------------
        if adx_val >= cfg.ADX_VERY_STRONG_THRESHOLD:
            trend_strength = TrendStrengthEnum.VERY_STRONG
        elif adx_val >= cfg.ADX_STRONG_TREND_THRESHOLD:
            trend_strength = TrendStrengthEnum.STRONG
        elif adx_val >= cfg.ADX_TREND_THRESHOLD:
            trend_strength = TrendStrengthEnum.MODERATE
        elif adx_val >= 15.0:
            trend_strength = TrendStrengthEnum.WEAK
        else:
            trend_strength = TrendStrengthEnum.NONE

        # ----------------------------------------------------
        # 3. Volatility State Classification (Percentile-based)
        # ----------------------------------------------------
        volatility_state = VolatilityStateEnum.NORMAL
        if candles and len(candles) >= 10 and vol.atr is not None and last_close and last_close > 0:
            current_atr_pct = (vol.atr / last_close) * 100.0

            lookback = min(len(candles), cfg.VOLATILITY_LOOKBACK_BARS)
            subset_candles = candles[-lookback:]
            hist_atr_pcts = []
            for c in subset_candles:
                if c.close > 0:
                    candle_range_pct = ((c.high - c.low) / c.close) * 100.0
                    hist_atr_pcts.append(candle_range_pct)

            if hist_atr_pcts:
                arr = np.array(hist_atr_pcts)
                if np.max(arr) == np.min(arr) or np.ptp(arr) < 1e-4:
                    percentile = 0.50
                else:
                    percentile = float(np.mean(arr <= current_atr_pct))

                if percentile >= cfg.VOL_PERCENTILE_EXTREME:
                    volatility_state = VolatilityStateEnum.EXTREME
                    contradictions.append(
                        EvidenceItem(
                            category=EvidenceCategoryEnum.VOLATILITY,
                            description="Volatility: Extreme range expansion detected",
                            metric_value=f"ATR%: {current_atr_pct:.2f}% (Percentile {percentile * 100:.0f}%)",
                            is_supporting=False,
                        )
                    )
                elif percentile >= cfg.VOL_PERCENTILE_HIGH:
                    volatility_state = VolatilityStateEnum.HIGH
                elif percentile <= cfg.VOL_PERCENTILE_VERY_LOW:
                    volatility_state = VolatilityStateEnum.VERY_LOW
                    evidence.append(
                        EvidenceItem(
                            category=EvidenceCategoryEnum.VOLATILITY,
                            description="Volatility: Range compression / Low volatility",
                            metric_value=f"ATR%: {current_atr_pct:.2f}%",
                        )
                    )
                elif percentile <= cfg.VOL_PERCENTILE_LOW:
                    volatility_state = VolatilityStateEnum.LOW
                else:
                    volatility_state = VolatilityStateEnum.NORMAL

        # ----------------------------------------------------
        # 4. Momentum State Classification
        # ----------------------------------------------------
        rsi_val = mom.rsi or 50.0
        macd_hist = mom.macd_histogram or 0.0

        if rsi_val >= cfg.RSI_OVERBOUGHT_THRESHOLD:
            momentum_state = MomentumStateEnum.VERY_POSITIVE
            if direction == DirectionEnum.BULLISH:
                contradictions.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.MOMENTUM,
                        description="Momentum Warning: RSI in extended overbought territory",
                        metric_value=f"RSI: {rsi_val:.1f}",
                        is_supporting=False,
                    )
                )
        elif rsi_val <= cfg.RSI_OVERSOLD_THRESHOLD:
            momentum_state = MomentumStateEnum.VERY_NEGATIVE
            if direction == DirectionEnum.BEARISH:
                contradictions.append(
                    EvidenceItem(
                        category=EvidenceCategoryEnum.MOMENTUM,
                        description="Momentum Warning: RSI in extended oversold territory",
                        metric_value=f"RSI: {rsi_val:.1f}",
                        is_supporting=False,
                    )
                )
        elif rsi_val >= cfg.RSI_BULLISH_BIAS and macd_hist > 0:
            momentum_state = MomentumStateEnum.POSITIVE
            evidence.append(
                EvidenceItem(
                    category=EvidenceCategoryEnum.MOMENTUM,
                    description="Momentum: Positive momentum alignment (RSI > 50 & MACD Hist > 0)",
                    metric_value=f"RSI: {rsi_val:.1f}, Hist: {macd_hist:.2f}",
                )
            )
        elif rsi_val <= cfg.RSI_BEARISH_BIAS and macd_hist < 0:
            momentum_state = MomentumStateEnum.NEGATIVE
            evidence.append(
                EvidenceItem(
                    category=EvidenceCategoryEnum.MOMENTUM,
                    description="Momentum: Negative momentum alignment (RSI < 50 & MACD Hist < 0)",
                    metric_value=f"RSI: {rsi_val:.1f}, Hist: {macd_hist:.2f}",
                )
            )
        else:
            momentum_state = MomentumStateEnum.NEUTRAL

        # ----------------------------------------------------
        # 5. Volume State Classification
        # ----------------------------------------------------
        rvol = volume.relative_volume or 1.0
        if rvol >= 2.0:
            volume_state = VolumeStateEnum.HIGH_EXPANSION
            evidence.append(
                EvidenceItem(
                    category=EvidenceCategoryEnum.VOLUME,
                    description="Volume: Strong institutional volume expansion",
                    metric_value=f"RVol: {rvol:.2f}x",
                )
            )
        elif rvol >= cfg.RVOL_HIGH_THRESHOLD:
            volume_state = VolumeStateEnum.ABOVE_AVERAGE
        elif rvol <= cfg.RVOL_LOW_THRESHOLD:
            volume_state = VolumeStateEnum.LOW
        else:
            volume_state = VolumeStateEnum.NORMAL

        # ----------------------------------------------------
        # 6. Overall Market Regime Synthesis
        # ----------------------------------------------------
        if direction == DirectionEnum.BULLISH and trend_strength in [TrendStrengthEnum.MODERATE, TrendStrengthEnum.STRONG, TrendStrengthEnum.VERY_STRONG]:
            overall_regime = OverallRegimeEnum.TRENDING_BULLISH
        elif direction == DirectionEnum.BEARISH and trend_strength in [TrendStrengthEnum.MODERATE, TrendStrengthEnum.STRONG, TrendStrengthEnum.VERY_STRONG]:
            overall_regime = OverallRegimeEnum.TRENDING_BEARISH
        elif volatility_state == VolatilityStateEnum.EXTREME:
            overall_regime = OverallRegimeEnum.HIGH_VOLATILITY
        elif volatility_state == VolatilityStateEnum.VERY_LOW and trend_strength in [TrendStrengthEnum.NONE, TrendStrengthEnum.WEAK]:
            overall_regime = OverallRegimeEnum.LOW_VOLATILITY
        elif direction == DirectionEnum.RANGE or trend_strength == TrendStrengthEnum.NONE:
            overall_regime = OverallRegimeEnum.RANGING
        elif structure_state == StructureStateEnum.TRANSITION:
            overall_regime = OverallRegimeEnum.TRANSITION
        else:
            overall_regime = OverallRegimeEnum.UNCERTAIN

        # ----------------------------------------------------
        # 7. Evidence Strength (Rule Agreement Metric 0.0 - 100.0)
        # ----------------------------------------------------
        group_scores = {
            "trend": (bull_trend_votes / 4.0) if direction == DirectionEnum.BULLISH else ((bear_trend_votes / 4.0) if direction == DirectionEnum.BEARISH else 0.5),
            "momentum": 1.0 if (direction == DirectionEnum.BULLISH and momentum_state in [MomentumStateEnum.POSITIVE, MomentumStateEnum.VERY_POSITIVE]) or (direction == DirectionEnum.BEARISH and momentum_state in [MomentumStateEnum.NEGATIVE, MomentumStateEnum.VERY_NEGATIVE]) else (0.5 if momentum_state == MomentumStateEnum.NEUTRAL else 0.2),
            "structure": 1.0 if (direction == DirectionEnum.BULLISH and structure_state == StructureStateEnum.BULLISH) or (direction == DirectionEnum.BEARISH and structure_state == StructureStateEnum.BEARISH) else 0.5,
            "volatility": 0.3 if volatility_state == VolatilityStateEnum.EXTREME else (0.8 if volatility_state == VolatilityStateEnum.NORMAL else 0.6),
            "volume": 0.9 if volume_state in [VolumeStateEnum.ABOVE_AVERAGE, VolumeStateEnum.HIGH_EXPANSION] else 0.6,
        }

        weighted_strength = (
            group_scores["trend"] * cfg.WEIGHT_TREND
            + group_scores["momentum"] * cfg.WEIGHT_MOMENTUM
            + group_scores["structure"] * cfg.WEIGHT_STRUCTURE
            + group_scores["volatility"] * cfg.WEIGHT_VOLATILITY
            + group_scores["volume"] * cfg.WEIGHT_VOLUME
        ) * 100.0

        evidence_strength = round(float(np.clip(weighted_strength, 0.0, 100.0)), 1)

        return MarketRegimeSnapshot(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=ts,
            is_confirmed=is_confirmed,
            direction=direction,
            trend_strength=trend_strength,
            volatility_state=volatility_state,
            momentum_state=momentum_state,
            volume_state=volume_state,
            structure_state=structure_state,
            overall_regime=overall_regime,
            evidence_strength=evidence_strength,
            evidence=evidence,
            contradictions=contradictions,
            regime_engine_version=cfg.regime_engine_version,
            regime_config_version=cfg.regime_config_version,
        )
