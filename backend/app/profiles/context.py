"""
Multi-Timeframe Context Engine for Phase 12 Trading Profiles.
Enforces strictly causal synchronization without higher-timeframe future leakage.
"""

from typing import Dict, List, Optional
from app.data.schema import Candle, MarketDataQuality, QualityStatusEnum
from app.indicators.engine import IndicatorEngine
from app.regime.engine import MarketRegimeEngine
from app.structure.engine import MarketStructureEngine
from app.signals.engine import MultiFactorSignalEngine
from app.profiles.models import MultiTimeframeContext, TradingProfileConfig


def get_tf_ms(tf: str) -> int:
    unit = tf[-1].lower()
    val = int(tf[:-1])
    if unit == "m":
        return val * 60 * 1000
    if unit == "h":
        return val * 3600 * 1000
    if unit == "d":
        return val * 86400 * 1000
    if unit == "w":
        return val * 7 * 86400 * 1000
    return 60000


class MultiTimeframeContextBuilder:
    """
    Builds a synchronized, causally validated multi-timeframe analytical context.
    Guarantees that context candles are closed as of the primary candle's close time.
    """

    @classmethod
    def build_context(
        cls,
        symbol: str,
        profile_config: TradingProfileConfig,
        primary_candles: List[Candle],
        context_candles_map: Dict[str, List[Candle]],
        is_confirmed: bool = True,
    ) -> MultiTimeframeContext:
        if not primary_candles:
            raise ValueError("Primary candle series cannot be empty")

        primary_candle = primary_candles[-1]
        analytical_ts = primary_candle.timestamp
        prim_ms = get_tf_ms(profile_config.primary_timeframe)
        primary_close_ts = primary_candle.close_time if primary_candle.close_time else (primary_candle.timestamp + prim_ms - 1)

        context = MultiTimeframeContext(
            symbol=symbol,
            primary_timeframe=profile_config.primary_timeframe,
            analytical_timestamp=analytical_ts,
            primary_candle=primary_candle,
            context_timeframes=profile_config.context_timeframes,
            is_causally_valid=True,
            validation_messages=[],
        )

        # 1. Process Primary Timeframe Analytics
        try:
            prim_ind = IndicatorEngine.calculate_snapshot(
                primary_candles, symbol=symbol, timeframe=profile_config.primary_timeframe, is_confirmed=is_confirmed
            )
            prim_struct = MarketStructureEngine.evaluate(
                primary_candles, indicators=prim_ind, is_confirmed=is_confirmed
            )
            prim_regime = MarketRegimeEngine.classify(
                candles=primary_candles, indicators=prim_ind, structure_state=prim_struct.structure_direction, is_confirmed=is_confirmed
            )
            prim_sig = MultiFactorSignalEngine.calculate_signal(
                candles=primary_candles, indicators=prim_ind, regime=prim_regime, structure=prim_struct, is_confirmed=is_confirmed
            )
            prim_qual = MarketDataQuality(
                symbol=symbol,
                timeframe=profile_config.primary_timeframe,
                status=QualityStatusEnum.HEALTHY,
                candle_count=len(primary_candles),
                stale=False,
            )

            context.context_candles[profile_config.primary_timeframe] = primary_candle
            context.context_indicators[profile_config.primary_timeframe] = prim_ind
            context.context_structures[profile_config.primary_timeframe] = prim_struct
            context.context_regimes[profile_config.primary_timeframe] = prim_regime
            context.context_signals[profile_config.primary_timeframe] = prim_sig
            context.context_qualities[profile_config.primary_timeframe] = prim_qual
        except Exception as e:
            context.is_causally_valid = False
            context.validation_messages.append(f"Primary timeframe evaluation error: {str(e)}")

        # 2. Process Higher Timeframe Contexts with Strict Causal Filtering
        for ctx_tf in profile_config.context_timeframes:
            ctx_series = context_candles_map.get(ctx_tf, [])
            ctx_ms = get_tf_ms(ctx_tf)
            
            # Filter candles that closed at or before primary candle's close time
            valid_ctx_candles = []
            for c in ctx_series:
                c_close = c.close_time if c.close_time else (c.timestamp + ctx_ms - 1)
                if c_close <= primary_close_ts and c.is_closed:
                    valid_ctx_candles.append(c)

            if not valid_ctx_candles:
                context.validation_messages.append(f"No closed context candles available for {ctx_tf}")
                continue

            # Anti-leakage assertion: latest context candle timestamp MUST be <= primary candle timestamp
            latest_ctx_candle = valid_ctx_candles[-1]
            if latest_ctx_candle.timestamp > analytical_ts:
                context.is_causally_valid = False
                context.validation_messages.append(
                    f"CAUSAL LEAKAGE DETECTED: {ctx_tf} candle ts ({latest_ctx_candle.timestamp}) > primary ts ({analytical_ts})"
                )
                continue

            try:
                ctx_ind = IndicatorEngine.calculate_snapshot(
                    valid_ctx_candles, symbol=symbol, timeframe=ctx_tf, is_confirmed=True
                )
                ctx_struct = MarketStructureEngine.evaluate(
                    valid_ctx_candles, indicators=ctx_ind, is_confirmed=True
                )
                ctx_regime = MarketRegimeEngine.classify(
                    candles=valid_ctx_candles, indicators=ctx_ind, structure_state=ctx_struct.structure_direction, is_confirmed=True
                )
                ctx_sig = MultiFactorSignalEngine.calculate_signal(
                    candles=valid_ctx_candles, indicators=ctx_ind, regime=ctx_regime, structure=ctx_struct, is_confirmed=True
                )
                ctx_qual = MarketDataQuality(
                    symbol=symbol,
                    timeframe=ctx_tf,
                    status=QualityStatusEnum.HEALTHY,
                    candle_count=len(valid_ctx_candles),
                    stale=False,
                )

                context.context_candles[ctx_tf] = latest_ctx_candle
                context.context_indicators[ctx_tf] = ctx_ind
                context.context_structures[ctx_tf] = ctx_struct
                context.context_regimes[ctx_tf] = ctx_regime
                context.context_signals[ctx_tf] = ctx_sig
                context.context_qualities[ctx_tf] = ctx_qual
            except Exception as e:
                context.validation_messages.append(f"Context {ctx_tf} evaluation error: {str(e)}")

        return context
