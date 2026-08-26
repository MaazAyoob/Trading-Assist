from typing import List, Optional, Tuple
import numpy as np
from app.data.schema import Candle, CandleStateEnum, QualityStatusEnum
from app.indicators.config import IndicatorConfig, default_indicator_config
from app.indicators.base import (
    IndicatorSnapshot,
    TrendIndicators,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
    IndicatorHistoryPoint,
    safe_float,
)
from app.indicators.trend import compute_ema, compute_rolling_vwap, compute_adx, compute_supertrend
from app.indicators.momentum import compute_rsi, compute_macd, compute_stoch_rsi, compute_roc
from app.indicators.volatility import compute_atr, compute_bollinger_bands
from app.indicators.volume import compute_volume_sma, compute_relative_volume, compute_obv


class IndicatorEngine:
    """
    Pure, deterministic quantitative indicator calculation engine.
    Architectural Guarantees:
    - Immutable: Never mutates input candle datasets.
    - Zero Future Leakage: Calculations only use historical observations up to calculation bar index.
    - Non-repainting: Confirmed snapshots generated from closed candles are immutable.
    - No Network / DB / FastAPI dependency: Usable identically in Live Streaming and Backtesting.
    - Strict NaN/Infinity sanitization: Never exposes NaN/Inf to consumers.
    """

    @classmethod
    def _extract_arrays(cls, candles: List[Candle]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Extract read-only numpy float arrays from candle sequence."""
        n = len(candles)
        timestamps = np.empty(n, dtype=np.int64)
        opens = np.empty(n, dtype=np.float64)
        highs = np.empty(n, dtype=np.float64)
        lows = np.empty(n, dtype=np.float64)
        closes = np.empty(n, dtype=np.float64)
        volumes = np.empty(n, dtype=np.float64)

        for i, c in enumerate(candles):
            timestamps[i] = c.timestamp
            opens[i] = c.open
            highs[i] = c.high
            lows[i] = c.low
            closes[i] = c.close
            volumes[i] = c.volume

        return timestamps, highs, lows, closes, volumes

    @classmethod
    def calculate_snapshot(
        cls,
        candles: List[Candle],
        symbol: str,
        timeframe: str,
        is_confirmed: bool = True,
        quality_status: QualityStatusEnum = QualityStatusEnum.HEALTHY,
        config: Optional[IndicatorConfig] = None,
    ) -> IndicatorSnapshot:
        """
        Calculate an IndicatorSnapshot for the current point in time.
        If is_confirmed=True, calculation uses only confirmed/closed candles.
        If is_confirmed=False, calculation includes the active forming/open candle.
        """
        cfg = config or default_indicator_config

        # Filter if confirmed mode requested
        dataset = [c for c in candles if c.is_closed or c.state == CandleStateEnum.CLOSED] if is_confirmed else list(candles)

        if not dataset:
            return IndicatorSnapshot(
                symbol=symbol.upper(),
                timeframe=timeframe,
                timestamp=0,
                is_confirmed=is_confirmed,
                quality_status=QualityStatusEnum.INSUFFICIENT_DATA,
                indicator_engine_version=cfg.indicator_engine_version,
                indicator_config_version=cfg.indicator_config_version,
                trend=TrendIndicators(),
                momentum=MomentumIndicators(),
                volatility=VolatilityIndicators(),
                volume=VolumeIndicators(),
            )

        timestamps, highs, lows, closes, volumes = cls._extract_arrays(dataset)
        last_idx = len(closes) - 1
        last_ts = int(timestamps[last_idx])

        # 1. Trend
        ema_9 = compute_ema(closes, 9)
        ema_21 = compute_ema(closes, 21)
        ema_50 = compute_ema(closes, 50)
        ema_100 = compute_ema(closes, 100)
        ema_200 = compute_ema(closes, 200)
        vwap = compute_rolling_vwap(timestamps, highs, lows, closes, volumes, cfg.VWAP_WINDOW_HOURS)
        adx, plus_di, minus_di = compute_adx(highs, lows, closes, cfg.ADX_PERIOD)
        supertrend, st_dir = compute_supertrend(highs, lows, closes, cfg.SUPERTREND_PERIOD, cfg.SUPERTREND_MULTIPLIER)

        trend = TrendIndicators(
            ema_9=safe_float(ema_9[last_idx]),
            ema_21=safe_float(ema_21[last_idx]),
            ema_50=safe_float(ema_50[last_idx]),
            ema_100=safe_float(ema_100[last_idx]),
            ema_200=safe_float(ema_200[last_idx]),
            vwap=safe_float(vwap[last_idx]),
            adx=safe_float(adx[last_idx]),
            plus_di=safe_float(plus_di[last_idx]),
            minus_di=safe_float(minus_di[last_idx]),
            supertrend=safe_float(supertrend[last_idx]),
            supertrend_direction=int(st_dir[last_idx]) if not np.isnan(st_dir[last_idx]) else None,
        )

        # 2. Momentum
        rsi = compute_rsi(closes, cfg.RSI_PERIOD)
        macd, macd_sig, macd_hist = compute_macd(closes, cfg.MACD_FAST, cfg.MACD_SLOW, cfg.MACD_SIGNAL)
        stoch_k, stoch_d = compute_stoch_rsi(closes, cfg.STOCH_RSI_PERIOD, cfg.STOCH_RSI_K, cfg.STOCH_RSI_D)
        roc = compute_roc(closes, cfg.ROC_PERIOD)

        momentum = MomentumIndicators(
            rsi=safe_float(rsi[last_idx]),
            macd=safe_float(macd[last_idx]),
            macd_signal=safe_float(macd_sig[last_idx]),
            macd_histogram=safe_float(macd_hist[last_idx]),
            stoch_rsi_k=safe_float(stoch_k[last_idx]),
            stoch_rsi_d=safe_float(stoch_d[last_idx]),
            roc=safe_float(roc[last_idx]),
        )

        # 3. Volatility
        atr = compute_atr(highs, lows, closes, cfg.ATR_PERIOD)
        bb_u, bb_m, bb_l, bb_w, bb_pb = compute_bollinger_bands(closes, cfg.BB_PERIOD, cfg.BB_STD)

        volatility = VolatilityIndicators(
            atr=safe_float(atr[last_idx]),
            bb_upper=safe_float(bb_u[last_idx]),
            bb_middle=safe_float(bb_m[last_idx]),
            bb_lower=safe_float(bb_l[last_idx]),
            bb_bandwidth=safe_float(bb_w[last_idx]),
            bb_percent_b=safe_float(bb_pb[last_idx]),
        )

        # 4. Volume
        vol_sma = compute_volume_sma(volumes, cfg.VOLUME_SMA_PERIOD)
        rel_vol = compute_relative_volume(volumes, cfg.VOLUME_SMA_PERIOD)
        obv = compute_obv(closes, volumes)

        volume = VolumeIndicators(
            volume_sma=safe_float(vol_sma[last_idx]),
            relative_volume=safe_float(rel_vol[last_idx]),
            obv=safe_float(obv[last_idx]),
        )

        return IndicatorSnapshot(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=last_ts,
            is_confirmed=is_confirmed,
            quality_status=quality_status,
            indicator_engine_version=cfg.indicator_engine_version,
            indicator_config_version=cfg.indicator_config_version,
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            volume=volume,
        )

    @classmethod
    def calculate_history(
        cls,
        candles: List[Candle],
        symbol: str,
        timeframe: str,
        limit: int = 300,
        config: Optional[IndicatorConfig] = None,
    ) -> List[IndicatorHistoryPoint]:
        """
        Calculate historical series aligned bar-by-bar with input candles for charts.
        """
        cfg = config or default_indicator_config
        n = len(candles)
        if n == 0:
            return []

        timestamps, highs, lows, closes, volumes = cls._extract_arrays(candles)

        ema_9 = compute_ema(closes, 9)
        ema_21 = compute_ema(closes, 21)
        ema_50 = compute_ema(closes, 50)
        ema_200 = compute_ema(closes, 200)
        vwap = compute_rolling_vwap(timestamps, highs, lows, closes, volumes, cfg.VWAP_WINDOW_HOURS)
        supertrend, st_dir = compute_supertrend(highs, lows, closes, cfg.SUPERTREND_PERIOD, cfg.SUPERTREND_MULTIPLIER)

        bb_u, bb_m, bb_l, _, _ = compute_bollinger_bands(closes, cfg.BB_PERIOD, cfg.BB_STD)
        rsi = compute_rsi(closes, cfg.RSI_PERIOD)
        macd, macd_sig, macd_hist = compute_macd(closes, cfg.MACD_FAST, cfg.MACD_SLOW, cfg.MACD_SIGNAL)

        start_idx = max(0, n - limit)
        history: List[IndicatorHistoryPoint] = []

        for i in range(start_idx, n):
            c = candles[i]
            history.append(
                IndicatorHistoryPoint(
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    is_closed=c.is_closed,
                    ema_9=safe_float(ema_9[i]),
                    ema_21=safe_float(ema_21[i]),
                    ema_50=safe_float(ema_50[i]),
                    ema_200=safe_float(ema_200[i]),
                    vwap=safe_float(vwap[i]),
                    supertrend=safe_float(supertrend[i]),
                    supertrend_direction=int(st_dir[i]) if not np.isnan(st_dir[i]) else None,
                    bb_upper=safe_float(bb_u[i]),
                    bb_middle=safe_float(bb_m[i]),
                    bb_lower=safe_float(bb_l[i]),
                    rsi=safe_float(rsi[i]),
                    macd=safe_float(macd[i]),
                    macd_signal=safe_float(macd_sig[i]),
                    macd_histogram=safe_float(macd_hist[i]),
                )
            )

        return history
