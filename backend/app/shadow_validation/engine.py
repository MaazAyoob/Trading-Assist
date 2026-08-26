"""
Phase 9 — Real-Time Shadow Validation Engine.
Evaluates confirmed CLOSED candles causally against Baseline, A2, and E2 candidate streams.
"""

import time
from typing import List, Dict, Optional, Tuple, Set
import numpy as np

from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.indicators.trend import compute_ema, compute_rolling_vwap, compute_adx, compute_supertrend
from app.indicators.momentum import compute_rsi, compute_macd, compute_stoch_rsi, compute_roc
from app.indicators.volatility import compute_atr, compute_bollinger_bands
from app.indicators.volume import compute_volume_sma, compute_relative_volume, compute_obv
from app.indicators.base import (
    safe_float, IndicatorSnapshot, TrendIndicators, MomentumIndicators,
    VolatilityIndicators, VolumeIndicators
)
from app.structure.config import default_structure_config
from app.structure.models import SwingTypeEnum, SwingPoint, MarketStructureSnapshot, ZoneStatusEnum
from app.structure.levels import cluster_support_resistance_zones
from app.regime.engine import MarketRegimeEngine
from app.signals.models import SignalDirectionEnum, SignalStatusEnum
from app.signals.engine import MultiFactorSignalEngine
from app.strategy_research.experiments import PullbackResearchFilter, ExtensionResearchFilter
from app.shadow_validation.models import ShadowSignal, HorizonOutcome, HorizonStatusEnum
from app.shadow_validation.config import HORIZONS, CANDIDATES
from app.core.logging import logger


class ShadowValidationEngine:
    """
    Real-time shadow evaluator. Generates immutable signal snapshots for Baseline, A2, and E2.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.processed_signal_keys: Set[str] = set()

    def process_closed_candle(
        self,
        candles: List[Candle],
        quality: MarketDataQuality,
        session_config_hashes: Dict[str, str],
        received_timestamp: Optional[int] = None,
    ) -> List[ShadowSignal]:
        """
        Evaluates the latest confirmed CLOSED candle strictly using causal history (candles <= T).
        Returns a list of immutable ShadowSignal snapshots generated across the 3 isolated candidate streams.
        """
        t_start = time.perf_counter()
        if not candles:
            return []

        cur_candle = candles[-1]
        # Safety Check: Candlestick closure verification
        if not cur_candle.is_closed:
            logger.warning("ShadowValidationEngine: Rejected non-closed candle.")
            return []

        # Data Quality Check: Abort signal generation if quality status is invalid or insufficient
        if quality.status in [QualityStatusEnum.INVALID, QualityStatusEnum.INSUFFICIENT_DATA, QualityStatusEnum.OFFLINE]:
            logger.warning(f"ShadowValidationEngine: Signal generation suppressed due to data quality status '{quality.status.value}'.")
            return []

        n = len(candles)
        if n < 50:
            return []

        # Extract causal arrays for indicators
        timestamps, highs, lows, closes, volumes = IndicatorEngine._extract_arrays(candles)
        cur_close_time = int(cur_candle.close_time if cur_candle.close_time else (cur_candle.timestamp + 899999))
        cur_open_time = int(cur_candle.timestamp)
        close_p = float(cur_candle.close)

        # 1. Compute Indicators
        atr_arr = compute_atr(highs, lows, closes, 14)
        cur_atr = float(atr_arr[-1]) if not np.isnan(atr_arr[-1]) else 1.0

        ema9 = compute_ema(closes, 9)
        ema21 = compute_ema(closes, 21)
        ema50 = compute_ema(closes, 50)
        ema100 = compute_ema(closes, 100)
        ema200 = compute_ema(closes, 200)
        vwap_arr = compute_rolling_vwap(timestamps, highs, lows, closes, volumes, 24)
        adx_arr, pdi_arr, mdi_arr = compute_adx(highs, lows, closes, 14)
        st_arr, st_dir_arr = compute_supertrend(highs, lows, closes, 10, 3.0)
        rsi_arr = compute_rsi(closes, 14)
        macd_arr, macd_sig_arr, macd_hist_arr = compute_macd(closes, 12, 26, 9)
        stoch_k_arr, stoch_d_arr = compute_stoch_rsi(closes, 14, 3, 3)
        roc_arr = compute_roc(closes, 12)
        bbu_arr, bbm_arr, bbl_arr, bbw_arr, bbpb_arr = compute_bollinger_bands(closes, 20, 2.0)
        vol_sma_arr = compute_volume_sma(volumes, 20)
        rvol_arr = compute_relative_volume(volumes, 20)
        obv_arr = compute_obv(closes, volumes)

        vsma = float(vol_sma_arr[-1]) if not np.isnan(vol_sma_arr[-1]) and vol_sma_arr[-1] > 0 else float(cur_candle.volume or 1.0)

        indicators = IndicatorSnapshot(
            symbol=cur_candle.symbol if hasattr(cur_candle, "symbol") else "BTCUSDT",
            timeframe="15m",
            timestamp=cur_close_time,
            is_confirmed=True,
            trend=TrendIndicators(
                ema_9=safe_float(ema9[-1]), ema_21=safe_float(ema21[-1]), ema_50=safe_float(ema50[-1]),
                ema_100=safe_float(ema100[-1]), ema_200=safe_float(ema200[-1]),
                vwap=safe_float(vwap_arr[-1]), adx=safe_float(adx_arr[-1]),
                plus_di=safe_float(pdi_arr[-1]), minus_di=safe_float(mdi_arr[-1]),
                supertrend=safe_float(st_arr[-1]),
                supertrend_direction=int(st_dir_arr[-1]) if not np.isnan(st_dir_arr[-1]) else None,
            ),
            momentum=MomentumIndicators(
                rsi=safe_float(rsi_arr[-1]), macd=safe_float(macd_arr[-1]),
                macd_signal=safe_float(macd_sig_arr[-1]), macd_histogram=safe_float(macd_hist_arr[-1]),
                stoch_rsi_k=safe_float(stoch_k_arr[-1]), stoch_rsi_d=safe_float(stoch_d_arr[-1]),
                roc=safe_float(roc_arr[-1]),
            ),
            volatility=VolatilityIndicators(
                atr=safe_float(cur_atr), bb_upper=safe_float(bbu_arr[-1]), bb_middle=safe_float(bbm_arr[-1]),
                bb_lower=safe_float(bbl_arr[-1]), bb_bandwidth=safe_float(bbw_arr[-1]),
                bb_percent_b=safe_float(bbpb_arr[-1]),
            ),
            volume=VolumeIndicators(
                volume_sma=safe_float(vsma), relative_volume=safe_float(rvol_arr[-1]),
                obv=safe_float(obv_arr[-1]),
            ),
        )

        # 2. Compute Market Structure causally
        cfg_struct = default_structure_config
        left, right = cfg_struct.SWING_LEFT, cfg_struct.SWING_RIGHT
        acc_swings = []
        confirmed_shs = []
        confirmed_sls = []

        for k in range(n):
            j = k - right
            if j >= left:
                c_atr_j = float(atr_arr[j]) if not np.isnan(atr_arr[j]) else 1.0
                tol = cfg_struct.EQUAL_TOLERANCE_ATR * c_atr_j
                if (all(highs[j - m] <= highs[j] for m in range(1, left + 1)) and
                        all(highs[j + m] <= highs[j] + tol for m in range(1, right + 1))):
                    sp = SwingPoint(
                        id=f"SH_{int(timestamps[j])}", type=SwingTypeEnum.SWING_HIGH,
                        price=float(highs[j]), swing_timestamp=int(timestamps[j]),
                        confirmation_timestamp=int(timestamps[k]),
                        is_confirmed=True, volume=float(volumes[j]),
                    )
                    acc_swings.append(sp)
                    confirmed_shs.append(sp)
                if (all(lows[j - m] >= lows[j] for m in range(1, left + 1)) and
                        all(lows[j + m] >= lows[j] - tol for m in range(1, right + 1))):
                    sp = SwingPoint(
                        id=f"SL_{int(timestamps[j])}", type=SwingTypeEnum.SWING_LOW,
                        price=float(lows[j]), swing_timestamp=int(timestamps[j]),
                        confirmation_timestamp=int(timestamps[k]),
                        is_confirmed=True, volume=float(volumes[j]),
                    )
                    acc_swings.append(sp)
                    confirmed_sls.append(sp)

        if len(confirmed_shs) >= 2 and len(confirmed_sls) >= 2:
            p_sh, c_sh = confirmed_shs[-2], confirmed_shs[-1]
            p_sl, c_sl = confirmed_sls[-2], confirmed_sls[-1]
            if c_sh.price > p_sh.price and c_sl.price > p_sl.price:
                struct_dir = "BULLISH"
            elif c_sh.price < p_sh.price and c_sl.price < p_sl.price:
                struct_dir = "BEARISH"
            else:
                struct_dir = "RANGE"
        else:
            struct_dir = "UNKNOWN"

        recent_swings = acc_swings[-50:] if acc_swings else []
        sup_zones, res_zones = cluster_support_resistance_zones([cur_candle], recent_swings, cur_atr, cfg_struct)

        structure = MarketStructureSnapshot(
            symbol="BTCUSDT", timeframe="15m", timestamp=cur_close_time,
            is_confirmed=True, structure_direction=struct_dir,
            active_structural_high=confirmed_shs[-1] if confirmed_shs else None,
            active_structural_low=confirmed_sls[-1] if confirmed_sls else None,
            confirmed_swings=recent_swings, developing_swings=[],
            bos_events=[], choch_events=[],
            support_zones=sup_zones, resistance_zones=res_zones,
            structure_engine_version=cfg_struct.structure_engine_version,
            structure_config_version=cfg_struct.structure_config_version,
        )

        # 3. Classify Regime causally
        VOL_LOOKBACK = 50
        regime_start = max(0, n - VOL_LOOKBACK)
        regime = MarketRegimeEngine.classify(
            candles=candles[regime_start:], indicators=indicators,
            structure_state=structure.structure_direction, is_confirmed=True,
        )

        # 4. Compute Base Multi-Factor Signal
        sig = MultiFactorSignalEngine.calculate_signal(
            candles=[cur_candle], indicators=indicators,
            regime=regime, structure=structure, quality=quality, is_confirmed=True,
        )

        if sig.direction not in [SignalDirectionEnum.LONG_SETUP, SignalDirectionEnum.SHORT_SETUP] or sig.status != SignalStatusEnum.VALID:
            return []

        cur_vwap = indicators.trend.vwap
        vwap_dist_atr = round(abs(close_p - cur_vwap) / cur_atr, 3) if cur_vwap and cur_atr > 0 else None
        cur_ema21 = indicators.trend.ema_21
        ema21_dist_atr = round(abs(close_p - cur_ema21) / cur_atr, 3) if cur_ema21 and cur_atr > 0 else None

        generated_signals: List[ShadowSignal] = []
        now_ms = int(time.time() * 1000)
        t_recv = received_timestamp or now_ms
        latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        # --- CANDIDATE 1: BASELINE (Phase 5) ---
        base_key = f"BASELINE:BTCUSDT:15m:{cur_close_time}"
        if base_key not in self.processed_signal_keys:
            self.processed_signal_keys.add(base_key)
            init_outcomes = {h: HorizonOutcome(horizon=h, status=HorizonStatusEnum.PENDING) for h in HORIZONS}
            generated_signals.append(ShadowSignal(
                signal_id=f"SHADOW_BASELINE_{cur_close_time}",
                session_id=self.session_id,
                candidate_id="BASELINE",
                symbol="BTCUSDT",
                timeframe="15m",
                candle_index=n - 1,
                candle_open_time=cur_open_time,
                candle_close_time=cur_close_time,
                entry_reference_price=close_p,
                direction=sig.direction.value,
                signal_score=sig.score,
                signal_strength=sig.strength.value,
                regime=regime.overall_regime.value if hasattr(regime.overall_regime, "value") else str(regime.overall_regime),
                structure_state=structure.structure_direction,
                volatility_state=regime.volatility_state.value if hasattr(regime.volatility_state, "value") else str(regime.volatility_state),
                trend_score=sig.evidence_groups["TREND"].score,
                momentum_score=sig.evidence_groups["MOMENTUM"].score,
                structure_score=sig.evidence_groups["STRUCTURE"].score,
                volume_score=sig.evidence_groups["VOLUME"].score,
                volatility_score=sig.evidence_groups.get("VOLATILITY", sig.evidence_groups["TREND"]).score,
                regime_score=sig.evidence_groups.get("REGIME", sig.evidence_groups["TREND"]).score,
                vwap_price=cur_vwap,
                vwap_distance_atr=vwap_dist_atr,
                ema21_price=cur_ema21,
                ema21_distance_atr=ema21_dist_atr,
                atr=cur_atr,
                data_quality_status=quality.status.value,
                engine_version="0.5.0",
                strategy_config_hash=session_config_hashes.get("phase5_signal_engine_hash", ""),
                causal_timestamp=cur_close_time,
                received_at_timestamp=t_recv,
                processing_latency_ms=latency_ms,
                outcomes=init_outcomes,
            ))

        # --- CANDIDATE 2: EXP_A2_PULLBACK_VWAP ---
        if PullbackResearchFilter.evaluate(cur_candle, indicators, sig.direction, "VWAP", 0.75):
            a2_key = f"EXP_A2_PULLBACK_VWAP:BTCUSDT:15m:{cur_close_time}"
            if a2_key not in self.processed_signal_keys:
                self.processed_signal_keys.add(a2_key)
                init_outcomes = {h: HorizonOutcome(horizon=h, status=HorizonStatusEnum.PENDING) for h in HORIZONS}
                generated_signals.append(ShadowSignal(
                    signal_id=f"SHADOW_EXP_A2_{cur_close_time}",
                    session_id=self.session_id,
                    candidate_id="EXP_A2_PULLBACK_VWAP",
                    symbol="BTCUSDT",
                    timeframe="15m",
                    candle_index=n - 1,
                    candle_open_time=cur_open_time,
                    candle_close_time=cur_close_time,
                    entry_reference_price=close_p,
                    direction=sig.direction.value,
                    signal_score=sig.score,
                    signal_strength=sig.strength.value,
                    regime=regime.overall_regime.value if hasattr(regime.overall_regime, "value") else str(regime.overall_regime),
                    structure_state=structure.structure_direction,
                    volatility_state=regime.volatility_state.value if hasattr(regime.volatility_state, "value") else str(regime.volatility_state),
                    trend_score=sig.evidence_groups["TREND"].score,
                    momentum_score=sig.evidence_groups["MOMENTUM"].score,
                    structure_score=sig.evidence_groups["STRUCTURE"].score,
                    volume_score=sig.evidence_groups["VOLUME"].score,
                    volatility_score=sig.evidence_groups.get("VOLATILITY", sig.evidence_groups["TREND"]).score,
                    regime_score=sig.evidence_groups.get("REGIME", sig.evidence_groups["TREND"]).score,
                    vwap_price=cur_vwap,
                    vwap_distance_atr=vwap_dist_atr,
                    ema21_price=cur_ema21,
                    ema21_distance_atr=ema21_dist_atr,
                    atr=cur_atr,
                    data_quality_status=quality.status.value,
                    engine_version="0.8.0-research",
                    strategy_config_hash=session_config_hashes.get("candidate_a2_config_hash", ""),
                    causal_timestamp=cur_close_time,
                    received_at_timestamp=t_recv,
                    processing_latency_ms=latency_ms,
                    outcomes=init_outcomes,
                ))

        # --- CANDIDATE 3: EXP_E2_EXTENSION_VWAP ---
        if ExtensionResearchFilter.evaluate(cur_candle, indicators, "VWAP_DISTANCE_ATR", 1.75):
            e2_key = f"EXP_E2_EXTENSION_VWAP:BTCUSDT:15m:{cur_close_time}"
            if e2_key not in self.processed_signal_keys:
                self.processed_signal_keys.add(e2_key)
                init_outcomes = {h: HorizonOutcome(horizon=h, status=HorizonStatusEnum.PENDING) for h in HORIZONS}
                generated_signals.append(ShadowSignal(
                    signal_id=f"SHADOW_EXP_E2_{cur_close_time}",
                    session_id=self.session_id,
                    candidate_id="EXP_E2_EXTENSION_VWAP",
                    symbol="BTCUSDT",
                    timeframe="15m",
                    candle_index=n - 1,
                    candle_open_time=cur_open_time,
                    candle_close_time=cur_close_time,
                    entry_reference_price=close_p,
                    direction=sig.direction.value,
                    signal_score=sig.score,
                    signal_strength=sig.strength.value,
                    regime=regime.overall_regime.value if hasattr(regime.overall_regime, "value") else str(regime.overall_regime),
                    structure_state=structure.structure_direction,
                    volatility_state=regime.volatility_state.value if hasattr(regime.volatility_state, "value") else str(regime.volatility_state),
                    trend_score=sig.evidence_groups["TREND"].score,
                    momentum_score=sig.evidence_groups["MOMENTUM"].score,
                    structure_score=sig.evidence_groups["STRUCTURE"].score,
                    volume_score=sig.evidence_groups["VOLUME"].score,
                    volatility_score=sig.evidence_groups.get("VOLATILITY", sig.evidence_groups["TREND"]).score,
                    regime_score=sig.evidence_groups.get("REGIME", sig.evidence_groups["TREND"]).score,
                    vwap_price=cur_vwap,
                    vwap_distance_atr=vwap_dist_atr,
                    ema21_price=cur_ema21,
                    ema21_distance_atr=ema21_dist_atr,
                    atr=cur_atr,
                    data_quality_status=quality.status.value,
                    engine_version="0.8.0-research",
                    strategy_config_hash=session_config_hashes.get("candidate_e2_config_hash", ""),
                    causal_timestamp=cur_close_time,
                    received_at_timestamp=t_recv,
                    processing_latency_ms=latency_ms,
                    outcomes=init_outcomes,
                ))

        return generated_signals
