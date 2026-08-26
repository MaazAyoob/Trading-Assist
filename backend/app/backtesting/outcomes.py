"""
Forward-return, Maximum Favorable Excursion (MFE), and Maximum Adverse Excursion (MAE) outcome calculators.
Strictly non-executing, analytical outcome framework.
"""

from typing import List, Dict, Optional
from app.data.schema import Candle
from app.signals.models import ResearchSignal, SignalDirectionEnum
from app.backtesting.models import (
    HorizonOutcome,
    SignalOutcome,
    OutcomeClassificationEnum,
)
from app.backtesting.config import CostModelConfig


class OutcomeCalculator:
    """
    Computes forward analytical returns and excursions across multiple horizons
    with strict forward-looking boundary isolation.
    """

    @staticmethod
    def evaluate_signal_outcomes(
        signal: ResearchSignal,
        signal_candle_idx: int,
        all_candles: List[Candle],
        horizons: List[int],
        cost_model: Optional[CostModelConfig] = None,
    ) -> SignalOutcome:
        """
        Calculates HorizonOutcome for each requested horizon for a confirmed signal at signal_candle_idx.
        Future window for horizon H strictly starts at index i + 1 up to i + H.
        """
        total_candles = len(all_candles)
        entry_price = signal.entry_reference_price if hasattr(signal, "entry_reference_price") and signal.entry_reference_price else all_candles[signal_candle_idx].close
        is_long = signal.direction == SignalDirectionEnum.LONG_SETUP

        outcomes: Dict[int, HorizonOutcome] = {}

        # Signal timestamp = candle close timestamp
        signal_candle = all_candles[signal_candle_idx]
        sig_ts = signal_candle.close_time if signal_candle.close_time else signal.timestamp

        for h in horizons:
            target_idx = signal_candle_idx + h
            if target_idx >= total_candles:
                # Incomplete horizon - never truncate or fabricate
                outcomes[h] = HorizonOutcome(
                    horizon=h,
                    future_close=None,
                    forward_return=None,
                    mfe=None,
                    mae=None,
                    status=OutcomeClassificationEnum.INSUFFICIENT_HORIZON,
                    estimated_net_forward_return=None,
                )
                continue

            # Future window strictly from i+1 to i+h (inclusive)
            future_window = all_candles[signal_candle_idx + 1 : target_idx + 1]
            future_close = all_candles[target_idx].close

            highs = [c.high for c in future_window]
            lows = [c.low for c in future_window]

            max_future_high = max(highs)
            min_future_low = min(lows)

            if is_long:
                # LONG Outcomes
                fwd_ret = (future_close - entry_price) / entry_price
                mfe = (max_future_high - entry_price) / entry_price
                mae = (min_future_low - entry_price) / entry_price
            else:
                # SHORT Outcomes
                fwd_ret = (entry_price - future_close) / entry_price
                mfe = (entry_price - min_future_low) / entry_price
                mae = (entry_price - max_future_high) / entry_price

            # Ensure MAE is non-positive for consistency
            if mae > 0:
                mae = 0.0
            # Ensure MFE is non-negative
            if mfe < 0:
                mfe = 0.0

            # Classification
            if fwd_ret > 1e-4:
                status = OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN
            elif fwd_ret < -1e-4:
                status = OutcomeClassificationEnum.NEGATIVE_FORWARD_RETURN
            else:
                status = OutcomeClassificationEnum.FLAT_FORWARD_RETURN

            # Optional cost scenario adjustment
            estimated_net = None
            if cost_model and cost_model.enabled:
                estimated_net = fwd_ret - cost_model.total_round_trip_fraction

            outcomes[h] = HorizonOutcome(
                horizon=h,
                future_close=future_close,
                forward_return=round(fwd_ret, 6),
                mfe=round(mfe, 6),
                mae=round(mae, 6),
                status=status,
                estimated_net_forward_return=round(estimated_net, 6) if estimated_net is not None else None,
            )

        regime_state = signal.evidence_groups.get("REGIME", None)
        regime_str = regime_state.state if regime_state else "UNKNOWN"

        structure_state = signal.evidence_groups.get("STRUCTURE", None)
        structure_str = structure_state.state if structure_state else "UNKNOWN"

        return SignalOutcome(
            signal_id=f"{signal.symbol}_{signal.timeframe}_{sig_ts}_{signal.direction.value}",
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            signal_timestamp=sig_ts,
            signal_direction=signal.direction.value,
            signal_strength=signal.strength.value,
            signal_score=signal.score,
            entry_reference_price=entry_price,
            outcomes=outcomes,
            regime_at_signal=regime_str,
            structure_at_signal=structure_str,
            volatility_at_signal="NORMAL",  # Enriched by engine if available
            engine_version=signal.engine_version,
            config_version=signal.config_version,
        )
