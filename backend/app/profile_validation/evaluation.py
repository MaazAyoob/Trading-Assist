"""
Evaluation Runner for Profile Validation Lab.
"""

from typing import Dict, List, Any
from app.data.schema import Candle
from app.profiles.models import TradingProfileConfig, ProfileStateEnum
from app.profiles.engine import TradingProfileEngine
from app.profile_validation.metrics import ProfileValidationMetricsCalculator


class ProfileEvaluationRunner:
    @classmethod
    def evaluate_profile_over_dataset(
        cls,
        symbol: str,
        profile_config: TradingProfileConfig,
        multi_tf_dataset: Dict[str, List[Candle]],
        warmup_bars: int = 60,
    ) -> Dict[str, Any]:
        prim_tf = profile_config.primary_timeframe
        primary_candles = multi_tf_dataset.get(prim_tf, [])

        if len(primary_candles) <= warmup_bars:
            return {"status": "INSUFFICIENT_HISTORY", "total_bars": len(primary_candles)}

        entry_prices: List[float] = []
        future_closes: List[List[float]] = []
        future_highs: List[List[float]] = []
        future_lows: List[List[float]] = []
        directions: List[str] = []
        signal_timestamps: List[int] = []

        tf_minutes = 1
        if prim_tf == "5m":
            tf_minutes = 5
        elif prim_tf == "15m":
            tf_minutes = 15
        elif prim_tf == "4h":
            tf_minutes = 240
        elif prim_tf == "1d":
            tf_minutes = 1440

        for i in range(warmup_bars, len(primary_candles)):
            window = primary_candles[:i]
            current_candle = window[-1]
            c_ts = current_candle.timestamp

            # Context slices: strictly at or before c_ts
            context_slice = {}
            for ctx_tf in profile_config.context_timeframes:
                all_ctx = multi_tf_dataset.get(ctx_tf, [])
                context_slice[ctx_tf] = [c for c in all_ctx if c.timestamp <= c_ts]

            result = TradingProfileEngine.evaluate_profile(
                symbol=symbol,
                profile_config=profile_config,
                primary_candles=window,
                context_candles_map=context_slice,
                is_confirmed=True,
            )

            if result.profile_state in (ProfileStateEnum.ENTRY_READY, ProfileStateEnum.SETUP) and result.trade_plan:
                tp = result.trade_plan
                if tp.decision.value in ("BUY", "SELL") and tp.entry:
                    entry_p = tp.entry.planned_entry_price
                    future_slice = primary_candles[i:i + 20]
                    if future_slice:
                        entry_prices.append(entry_p)
                        future_closes.append([c.close for c in future_slice])
                        future_highs.append([c.high for c in future_slice])
                        future_lows.append([c.low for c in future_slice])
                        directions.append(tp.decision.value)
                        signal_timestamps.append(c_ts)

        # Calculate metrics
        forward_returns = ProfileValidationMetricsCalculator.calculate_forward_returns(
            entry_prices, future_closes, directions
        )
        excursions = ProfileValidationMetricsCalculator.calculate_excursions(
            entry_prices, future_highs, future_lows, directions, horizon=5
        )
        density = ProfileValidationMetricsCalculator.calculate_signal_density(
            signal_timestamps, len(primary_candles), tf_minutes
        )

        return {
            "profile_id": profile_config.profile_id,
            "symbol": symbol,
            "primary_timeframe": prim_tf,
            "total_bars_evaluated": len(primary_candles) - warmup_bars,
            "signal_density": density,
            "forward_returns": forward_returns,
            "excursions_5c": excursions,
            "total_signals_generated": len(signal_timestamps),
        }
