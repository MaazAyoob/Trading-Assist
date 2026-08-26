from typing import Dict, List, Optional
import numpy as np
from app.data.schema import Candle
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot, DirectionEnum, OverallRegimeEnum
from app.structure.models import MarketStructureSnapshot, SwingTypeEnum, StructureEventTypeEnum, BreakQualityEnum
from app.signals.config import SignalConfig, default_signal_config
from app.signals.models import EvidenceGroupScore, EvidenceComponent


class EvidenceExtractor:
    """
    Extracts and normalizes directional evidence across 4 independent groups:
    TREND, MOMENTUM, STRUCTURE, VOLUME.
    Every group produces a normalized score on [-100.0, +100.0] with auditable sub-components.
    """

    @classmethod
    def extract_trend_evidence(
        cls,
        indicators: IndicatorSnapshot,
        candles: List[Candle],
        config: Optional[SignalConfig] = None,
    ) -> EvidenceGroupScore:
        cfg = config or default_signal_config
        trend = indicators.trend
        components: List[EvidenceComponent] = []

        # 1. EMA Structure (Cap: 40.0)
        ema_contrib = 0.0
        ema_desc = "EMA alignment neutral"
        ema_dir = "NEUTRAL"
        if trend.ema_9 is not None and trend.ema_21 is not None and trend.ema_50 is not None:
            if trend.ema_9 > trend.ema_21 > trend.ema_50:
                if trend.ema_200 is not None and trend.ema_50 > trend.ema_200:
                    ema_contrib = 40.0
                    ema_desc = "Full Bullish Stack (9 > 21 > 50 > 200)"
                else:
                    ema_contrib = 30.0
                    ema_desc = "Bullish Stack (9 > 21 > 50)"
                ema_dir = "BULLISH"
            elif trend.ema_9 < trend.ema_21 < trend.ema_50:
                if trend.ema_200 is not None and trend.ema_50 < trend.ema_200:
                    ema_contrib = -40.0
                    ema_desc = "Full Bearish Stack (9 < 21 < 50 < 200)"
                else:
                    ema_contrib = -30.0
                    ema_desc = "Bearish Stack (9 < 21 < 50)"
                ema_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="EMA_STRUCTURE",
                raw_value=f"9:{trend.ema_9 or 0:.0f}, 21:{trend.ema_21 or 0:.0f}, 50:{trend.ema_50 or 0:.0f}",
                contribution=ema_contrib,
                direction=ema_dir,
                explanation=ema_desc,
            )
        )

        # 2. Supertrend (Cap: 20.0)
        st_contrib = 0.0
        st_desc = "Supertrend neutral"
        st_dir = "NEUTRAL"
        if trend.supertrend_direction == 1:
            st_contrib = 20.0
            st_desc = f"Supertrend Bullish boundary at {trend.supertrend or 0:.2f}"
            st_dir = "BULLISH"
        elif trend.supertrend_direction == -1:
            st_contrib = -20.0
            st_desc = f"Supertrend Bearish boundary at {trend.supertrend or 0:.2f}"
            st_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="SUPERTREND",
                raw_value=f"dir:{trend.supertrend_direction}",
                contribution=st_contrib,
                direction=st_dir,
                explanation=st_desc,
            )
        )

        # 3. ADX & Directional Movement (Cap: 25.0)
        adx_contrib = 0.0
        adx_desc = "ADX below trend threshold"
        adx_dir = "NEUTRAL"
        adx_val = trend.adx or 0.0
        p_di = trend.plus_di or 0.0
        m_di = trend.minus_di or 0.0

        if adx_val >= 25.0:
            if p_di > m_di:
                adx_contrib = min(25.0, 15.0 + (adx_val - 25.0) * 0.5)
                adx_desc = f"Strong Bullish Trend (+DI:{p_di:.1f} > -DI:{m_di:.1f}, ADX:{adx_val:.1f})"
                adx_dir = "BULLISH"
            elif m_di > p_di:
                adx_contrib = -min(25.0, 15.0 + (adx_val - 25.0) * 0.5)
                adx_desc = f"Strong Bearish Trend (-DI:{m_di:.1f} > +DI:{p_di:.1f}, ADX:{adx_val:.1f})"
                adx_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="ADX_DIRECTIONAL_MOVEMENT",
                raw_value=f"ADX:{adx_val:.1f}, +DI:{p_di:.1f}, -DI:{m_di:.1f}",
                contribution=adx_contrib,
                direction=adx_dir,
                explanation=adx_desc,
            )
        )

        # 4. VWAP Position (Cap: 15.0)
        vwap_contrib = 0.0
        vwap_desc = "Price near VWAP"
        vwap_dir = "NEUTRAL"
        last_close = candles[-1].close if candles else None
        if last_close is not None and trend.vwap is not None:
            if last_close > trend.vwap:
                vwap_contrib = 15.0
                vwap_desc = f"Price ({last_close:.2f}) above 24h Rolling VWAP ({trend.vwap:.2f})"
                vwap_dir = "BULLISH"
            else:
                vwap_contrib = -15.0
                vwap_desc = f"Price ({last_close:.2f}) below 24h Rolling VWAP ({trend.vwap:.2f})"
                vwap_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="VWAP_POSITION",
                raw_value=f"Close:{last_close or 0:.2f}, VWAP:{trend.vwap or 0:.2f}",
                contribution=vwap_contrib,
                direction=vwap_dir,
                explanation=vwap_desc,
            )
        )

        raw_score = sum(c.contribution for c in components)
        score = float(np.clip(raw_score, -100.0, 100.0))
        state = "BULLISH" if score >= 30.0 else ("BEARISH" if score <= -30.0 else "NEUTRAL")

        return EvidenceGroupScore(
            group_name="TREND",
            score=score,
            weight=cfg.WEIGHT_TREND,
            weighted_contribution=round(score * cfg.WEIGHT_TREND, 2),
            state=state,
            components=components,
        )

    @classmethod
    def extract_momentum_evidence(
        cls,
        indicators: IndicatorSnapshot,
        regime: Optional[MarketRegimeSnapshot] = None,
        config: Optional[SignalConfig] = None,
    ) -> EvidenceGroupScore:
        cfg = config or default_signal_config
        mom = indicators.momentum
        components: List[EvidenceComponent] = []

        # 1. Context-Aware RSI (Cap: 35.0)
        rsi_val = mom.rsi or 50.0
        rsi_contrib = 0.0
        rsi_dir = "NEUTRAL"
        rsi_desc = f"RSI neutral at {rsi_val:.1f}"

        is_trending_bull = regime and regime.direction == DirectionEnum.BULLISH
        is_trending_bear = regime and regime.direction == DirectionEnum.BEARISH

        if rsi_val >= 70.0:
            if is_trending_bull:
                rsi_contrib = 30.0
                rsi_desc = f"RSI ({rsi_val:.1f}) in strong bullish momentum continuation"
                rsi_dir = "BULLISH"
            else:
                rsi_contrib = 10.0
                rsi_desc = f"RSI ({rsi_val:.1f}) elevated/overextended in range"
                rsi_dir = "BULLISH"
        elif rsi_val <= 30.0:
            if is_trending_bear:
                rsi_contrib = -30.0
                rsi_desc = f"RSI ({rsi_val:.1f}) in strong bearish momentum continuation"
                rsi_dir = "BEARISH"
            else:
                rsi_contrib = -10.0
                rsi_desc = f"RSI ({rsi_val:.1f}) depressed/oversold in range"
                rsi_dir = "BEARISH"
        elif rsi_val >= 52.0:
            rsi_contrib = min(25.0, (rsi_val - 50.0) * 1.5)
            rsi_desc = f"RSI ({rsi_val:.1f}) bullish bias"
            rsi_dir = "BULLISH"
        elif rsi_val <= 48.0:
            rsi_contrib = -min(25.0, (50.0 - rsi_val) * 1.5)
            rsi_desc = f"RSI ({rsi_val:.1f}) bearish bias"
            rsi_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="RSI_MOMENTUM",
                raw_value=f"RSI:{rsi_val:.1f}",
                contribution=rsi_contrib,
                direction=rsi_dir,
                explanation=rsi_desc,
            )
        )

        # 2. MACD & Histogram (Cap: 30.0)
        macd_line = mom.macd or 0.0
        macd_hist = mom.macd_histogram or 0.0
        macd_contrib = 0.0
        macd_dir = "NEUTRAL"
        macd_desc = "MACD histogram neutral"

        if macd_line > 0 and macd_hist > 0:
            macd_contrib = 30.0
            macd_desc = f"MACD line ({macd_line:.2f}) and histogram ({macd_hist:.2f}) positive"
            macd_dir = "BULLISH"
        elif macd_line < 0 and macd_hist < 0:
            macd_contrib = -30.0
            macd_desc = f"MACD line ({macd_line:.2f}) and histogram ({macd_hist:.2f}) negative"
            macd_dir = "BEARISH"
        elif macd_hist > 0:
            macd_contrib = 15.0
            macd_desc = f"MACD histogram positive ({macd_hist:.2f})"
            macd_dir = "BULLISH"
        elif macd_hist < 0:
            macd_contrib = -15.0
            macd_desc = f"MACD histogram negative ({macd_hist:.2f})"
            macd_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="MACD_HISTOGRAM",
                raw_value=f"line:{macd_line:.2f}, hist:{macd_hist:.2f}",
                contribution=macd_contrib,
                direction=macd_dir,
                explanation=macd_desc,
            )
        )

        # 3. Stochastic RSI (Cap: 20.0)
        k_val = mom.stoch_rsi_k or 50.0
        d_val = mom.stoch_rsi_d or 50.0
        stoch_contrib = 0.0
        stoch_dir = "NEUTRAL"
        stoch_desc = "StochRSI neutral"

        if k_val > d_val and k_val >= 50.0:
            stoch_contrib = 20.0
            stoch_desc = f"StochRSI %K ({k_val:.1f}) > %D ({d_val:.1f}) in upper zone"
            stoch_dir = "BULLISH"
        elif k_val < d_val and k_val <= 50.0:
            stoch_contrib = -20.0
            stoch_desc = f"StochRSI %K ({k_val:.1f}) < %D ({d_val:.1f}) in lower zone"
            stoch_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="STOCH_RSI",
                raw_value=f"%K:{k_val:.1f}, %D:{d_val:.1f}",
                contribution=stoch_contrib,
                direction=stoch_dir,
                explanation=stoch_desc,
            )
        )

        # 4. Rate of Change (ROC) (Cap: 15.0)
        roc_val = mom.roc or 0.0
        roc_contrib = 0.0
        roc_dir = "NEUTRAL"
        roc_desc = "ROC neutral"

        if roc_val >= 1.0:
            roc_contrib = min(15.0, roc_val * 7.5)
            roc_desc = f"Positive velocity (ROC: +{roc_val:.2f}%)"
            roc_dir = "BULLISH"
        elif roc_val <= -1.0:
            roc_contrib = -min(15.0, abs(roc_val) * 7.5)
            roc_desc = f"Negative velocity (ROC: {roc_val:.2f}%)"
            roc_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="RATE_OF_CHANGE",
                raw_value=f"ROC:{roc_val:.2f}%",
                contribution=roc_contrib,
                direction=roc_dir,
                explanation=roc_desc,
            )
        )

        raw_score = sum(c.contribution for c in components)
        score = float(np.clip(raw_score, -100.0, 100.0))
        state = "POSITIVE" if score >= 30.0 else ("NEGATIVE" if score <= -30.0 else "NEUTRAL")

        return EvidenceGroupScore(
            group_name="MOMENTUM",
            score=score,
            weight=cfg.WEIGHT_MOMENTUM,
            weighted_contribution=round(score * cfg.WEIGHT_MOMENTUM, 2),
            state=state,
            components=components,
        )

    @classmethod
    def extract_structure_evidence(
        cls,
        structure: MarketStructureSnapshot,
        config: Optional[SignalConfig] = None,
    ) -> EvidenceGroupScore:
        cfg = config or default_signal_config
        components: List[EvidenceComponent] = []

        # 1. Structural Trend Direction (Cap: 40.0)
        dir_contrib = 0.0
        dir_name = structure.structure_direction
        dir_desc = f"Structure state is {dir_name}"
        dir_eval = "NEUTRAL"

        if dir_name == "BULLISH":
            dir_contrib = 40.0
            dir_desc = "Confirmed Higher Highs and Higher Lows sequence"
            dir_eval = "BULLISH"
        elif dir_name == "BEARISH":
            dir_contrib = -40.0
            dir_desc = "Confirmed Lower Highs and Lower Lows sequence"
            dir_eval = "BEARISH"
        elif dir_name == "TRANSITION":
            dir_contrib = 0.0
            dir_desc = "Market structure in transition state"

        components.append(
            EvidenceComponent(
                name="SWING_STRUCTURE_DIRECTION",
                raw_value=dir_name,
                contribution=dir_contrib,
                direction=dir_eval,
                explanation=dir_desc,
            )
        )

        # 2. Break of Structure (BOS) Events (Cap: 35.0)
        bos_contrib = 0.0
        bos_desc = "No recent BOS events"
        bos_dir = "NEUTRAL"

        if structure.bos_events:
            latest_bos = structure.bos_events[-1]
            multiplier = 1.0 if latest_bos.break_quality == BreakQualityEnum.STRONG_BREAK else (0.7 if latest_bos.break_quality == BreakQualityEnum.NORMAL_BREAK else 0.4)
            if latest_bos.event_type == StructureEventTypeEnum.BULLISH_BOS:
                bos_contrib = 35.0 * multiplier
                bos_desc = f"Confirmed Bullish BOS at ${latest_bos.broken_level:.2f} ({latest_bos.break_quality.value})"
                bos_dir = "BULLISH"
            elif latest_bos.event_type == StructureEventTypeEnum.BEARISH_BOS:
                bos_contrib = -35.0 * multiplier
                bos_desc = f"Confirmed Bearish BOS at ${latest_bos.broken_level:.2f} ({latest_bos.break_quality.value})"
                bos_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="BREAK_OF_STRUCTURE",
                raw_value=structure.bos_events[-1].event_type if structure.bos_events else "NONE",
                contribution=bos_contrib,
                direction=bos_dir,
                explanation=bos_desc,
            )
        )

        # 3. Change of Character (CHoCH) Transition (Cap: 25.0)
        choch_contrib = 0.0
        choch_desc = "No recent CHoCH transitions"
        choch_dir = "NEUTRAL"

        if structure.choch_events:
            latest_choch = structure.choch_events[-1]
            if latest_choch.event_type == StructureEventTypeEnum.BULLISH_CHOCH:
                choch_contrib = 25.0
                choch_desc = f"Confirmed Bullish CHoCH transition at ${latest_choch.broken_level:.2f}"
                choch_dir = "BULLISH"
            elif latest_choch.event_type == StructureEventTypeEnum.BEARISH_CHOCH:
                choch_contrib = -25.0
                choch_desc = f"Confirmed Bearish CHoCH transition at ${latest_choch.broken_level:.2f}"
                choch_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="CHANGE_OF_CHARACTER",
                raw_value=structure.choch_events[-1].event_type if structure.choch_events else "NONE",
                contribution=choch_contrib,
                direction=choch_dir,
                explanation=choch_desc,
            )
        )

        raw_score = sum(c.contribution for c in components)
        score = float(np.clip(raw_score, -100.0, 100.0))
        state = "BULLISH" if score >= 30.0 else ("BEARISH" if score <= -30.0 else "NEUTRAL")

        return EvidenceGroupScore(
            group_name="STRUCTURE",
            score=score,
            weight=cfg.WEIGHT_STRUCTURE,
            weighted_contribution=round(score * cfg.WEIGHT_STRUCTURE, 2),
            state=state,
            components=components,
        )

    @classmethod
    def extract_volume_evidence(
        cls,
        indicators: IndicatorSnapshot,
        structure: MarketStructureSnapshot,
        config: Optional[SignalConfig] = None,
    ) -> EvidenceGroupScore:
        cfg = config or default_signal_config
        volume = indicators.volume
        components: List[EvidenceComponent] = []

        rvol = volume.relative_volume or 1.0

        # 1. Relative Volume with Structural Context (Cap: 50.0)
        # High volume is directional only when coupled with confirmed directional structure
        rvol_contrib = 0.0
        rvol_dir = "NEUTRAL"
        rvol_desc = f"Relative Volume {rvol:.2f}x"

        struct_dir = structure.structure_direction
        if rvol >= 1.5:
            if struct_dir == "BULLISH":
                rvol_contrib = min(50.0, 25.0 + (rvol - 1.5) * 25.0)
                rvol_desc = f"Institutional volume expansion ({rvol:.2f}x) confirming bullish structure"
                rvol_dir = "BULLISH"
            elif struct_dir == "BEARISH":
                rvol_contrib = -min(50.0, 25.0 + (rvol - 1.5) * 25.0)
                rvol_desc = f"Institutional volume expansion ({rvol:.2f}x) confirming bearish structure"
                rvol_dir = "BEARISH"
            else:
                rvol_contrib = 0.0
                rvol_desc = f"High volume ({rvol:.2f}x) in neutral structure (neutral activity)"

        components.append(
            EvidenceComponent(
                name="RELATIVE_VOLUME",
                raw_value=f"RVol:{rvol:.2f}x",
                contribution=rvol_contrib,
                direction=rvol_dir,
                explanation=rvol_desc,
            )
        )

        # 2. On-Balance Volume Direction (Cap: 50.0)
        obv_val = volume.obv or 0.0
        obv_contrib = 0.0
        obv_dir = "NEUTRAL"
        obv_desc = f"OBV at {obv_val:.0f}"

        if struct_dir == "BULLISH" and obv_val > 0:
            obv_contrib = 40.0
            obv_desc = "On-Balance Volume accumulation supporting trend"
            obv_dir = "BULLISH"
        elif struct_dir == "BEARISH" and obv_val < 0:
            obv_contrib = -40.0
            obv_desc = "On-Balance Volume distribution supporting downtrend"
            obv_dir = "BEARISH"

        components.append(
            EvidenceComponent(
                name="ON_BALANCE_VOLUME",
                raw_value=f"OBV:{obv_val:.0f}",
                contribution=obv_contrib,
                direction=obv_dir,
                explanation=obv_desc,
            )
        )

        raw_score = sum(c.contribution for c in components)
        score = float(np.clip(raw_score, -100.0, 100.0))
        state = "CONFIRMING_BULL" if score >= 30.0 else ("CONFIRMING_BEAR" if score <= -30.0 else "NEUTRAL")

        return EvidenceGroupScore(
            group_name="VOLUME",
            score=score,
            weight=cfg.WEIGHT_VOLUME,
            weighted_contribution=round(score * cfg.WEIGHT_VOLUME, 2),
            state=state,
            components=components,
        )
