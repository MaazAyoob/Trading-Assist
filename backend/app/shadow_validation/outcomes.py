"""
Phase 9 — Shadow Outcome Observation Engine.
Monitors subsequent closed candles, updating forward returns, MFE, and MAE for active signals.
"""

from typing import List, Dict, Optional
import numpy as np

from app.data.schema import Candle
from app.shadow_validation.models import ShadowSignal, HorizonOutcome, HorizonStatusEnum
from app.shadow_validation.config import HORIZONS


class ShadowOutcomeEngine:
    """
    Asynchronous outcome observer. Updates horizon returns strictly as subsequent candles close.
    """

    @classmethod
    def update_pending_outcomes(
        cls,
        signals: List[ShadowSignal],
        all_candles: List[Candle],
    ) -> int:
        """
        Iterates over active signals and checks if subsequent closed candles satisfy pending horizons.
        Returns the count of newly completed horizon outcomes.
        """
        completed_count = 0
        n_candles = len(all_candles)
        if n_candles == 0:
            return 0

        # Build candle lookup by timestamp and index
        ts_to_idx = {int(c.timestamp): idx for idx, c in enumerate(all_candles)}

        for sig in signals:
            sig_idx = ts_to_idx.get(sig.candle_open_time)
            if sig_idx is None:
                continue

            entry_p = sig.entry_reference_price
            is_long = (sig.direction == "LONG_SETUP")

            for h in HORIZONS:
                outcome = sig.outcomes.get(h)
                if not outcome or outcome.status != HorizonStatusEnum.PENDING:
                    continue

                target_idx = sig_idx + h
                if target_idx < n_candles:
                    target_candle = all_candles[target_idx]
                    if not target_candle.is_closed:
                        continue  # Must wait for candle to be fully closed

                    target_close = float(target_candle.close)
                    target_close_time = int(target_candle.close_time if target_candle.close_time else (target_candle.timestamp + 899999))

                    # Raw analytical forward return
                    if is_long:
                        raw_ret = (target_close - entry_p) / entry_p
                    else:
                        raw_ret = (entry_p - target_close) / entry_p

                    # Cost sensitivity: 5 bps (0.0005) and 10 bps (0.0010)
                    cost_5bps = raw_ret - 0.0005
                    cost_10bps = raw_ret - 0.0010

                    # Compute MFE (Max Favorable) and MAE (Max Adverse) across interval [sig_idx+1, target_idx]
                    interval_candles = all_candles[sig_idx + 1:target_idx + 1]
                    if interval_candles:
                        if is_long:
                            max_p = max(float(c.high) for c in interval_candles)
                            min_p = min(float(c.low) for c in interval_candles)
                            mfe = (max_p - entry_p) / entry_p
                            mae = (min_p - entry_p) / entry_p
                        else:
                            max_p = max(float(c.high) for c in interval_candles)
                            min_p = min(float(c.low) for c in interval_candles)
                            mfe = (entry_p - min_p) / entry_p
                            mae = (entry_p - max_p) / entry_p
                    else:
                        mfe = max(0.0, raw_ret)
                        mae = min(0.0, raw_ret)

                    outcome.status = HorizonStatusEnum.COMPLETE
                    outcome.target_candle_close_time = target_close_time
                    outcome.target_close_price = round(target_close, 2)
                    outcome.raw_analytical_return = round(raw_ret, 6)
                    outcome.cost_adjusted_return_5bps = round(cost_5bps, 6)
                    outcome.cost_adjusted_return_10bps = round(cost_10bps, 6)
                    outcome.mfe = round(mfe, 6)
                    outcome.mae = round(mae, 6)
                    outcome.completed_at_timestamp = target_close_time
                    completed_count += 1

        return completed_count

    @classmethod
    def finalize_session_horizons(cls, signals: List[ShadowSignal]):
        """
        Marks any remaining PENDING horizons as INSUFFICIENT_HORIZON upon session stop.
        Does not fabricate outcomes or classify as win/loss.
        """
        for sig in signals:
            for h in HORIZONS:
                outcome = sig.outcomes.get(h)
                if outcome and outcome.status == HorizonStatusEnum.PENDING:
                    outcome.status = HorizonStatusEnum.INSUFFICIENT_HORIZON
