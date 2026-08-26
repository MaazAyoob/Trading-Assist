"""
Metrics calculation engine for Profile Validation Lab.
"""

from typing import Dict, List, Any
import numpy as np


class ProfileValidationMetricsCalculator:
    @staticmethod
    def calculate_forward_returns(
        entry_prices: List[float],
        future_candle_closes: List[List[float]],
        directions: List[str],
    ) -> Dict[str, Any]:
        """
        Calculates forward returns across standard horizons: 1C, 3C, 5C, 10C, 20C.
        """
        horizons = [1, 3, 5, 10, 20]
        results: Dict[str, List[float]] = {f"{h}C": [] for h in horizons}

        for entry_p, closes, direction in zip(entry_prices, future_candle_closes, directions):
            if entry_p <= 0:
                continue
            is_long = direction.upper() in ("BUY", "BULLISH")
            
            for h in horizons:
                if len(closes) >= h:
                    close_at_h = closes[h - 1]
                    raw_ret = ((close_at_h - entry_p) / entry_p) * 100.0 if is_long else ((entry_p - close_at_h) / entry_p) * 100.0
                    results[f"{h}C"].append(raw_ret)

        summary = {}
        for h_str, rets in results.items():
            if rets:
                arr = np.array(rets)
                summary[h_str] = {
                    "count": len(rets),
                    "mean_return_pct": round(float(np.mean(arr)), 4),
                    "median_return_pct": round(float(np.median(arr)), 4),
                    "positive_rate_pct": round(float(np.mean(arr > 0)) * 100.0, 2),
                    "std_dev": round(float(np.std(arr)), 4),
                }
            else:
                summary[h_str] = {
                    "count": 0,
                    "mean_return_pct": 0.0,
                    "median_return_pct": 0.0,
                    "positive_rate_pct": 0.0,
                    "std_dev": 0.0,
                }
        return summary

    @staticmethod
    def calculate_excursions(
        entry_prices: List[float],
        future_highs: List[List[float]],
        future_lows: List[List[float]],
        directions: List[str],
        horizon: int = 5,
    ) -> Dict[str, float]:
        """Calculates Maximum Favorable (MFE) and Adverse (MAE) excursions over horizon bars."""
        mfe_list = []
        mae_list = []

        for ep, highs, lows, dir_str in zip(entry_prices, future_highs, future_lows, directions):
            if ep <= 0:
                continue
            is_long = dir_str.upper() in ("BUY", "BULLISH")
            h_slice = highs[:horizon]
            l_slice = lows[:horizon]

            if not h_slice or not l_slice:
                continue

            max_h = max(h_slice)
            min_l = min(l_slice)

            if is_long:
                mfe = ((max_h - ep) / ep) * 100.0
                mae = ((ep - min_l) / ep) * 100.0
            else:
                mfe = ((ep - min_l) / ep) * 100.0
                mae = ((max_h - ep) / ep) * 100.0

            mfe_list.append(max(0.0, mfe))
            mae_list.append(max(0.0, mae))

        return {
            "avg_mfe_pct": round(float(np.mean(mfe_list)), 4) if mfe_list else 0.0,
            "avg_mae_pct": round(float(np.mean(mae_list)), 4) if mae_list else 0.0,
            "median_mfe_pct": round(float(np.median(mfe_list)), 4) if mfe_list else 0.0,
            "median_mae_pct": round(float(np.median(mae_list)), 4) if mae_list else 0.0,
        }

    @staticmethod
    def calculate_signal_density(
        signal_timestamps: List[int],
        total_candle_count: int,
        candle_minutes: int,
    ) -> Dict[str, float]:
        """Calculates frequency, density, and adjacent clustering."""
        if not signal_timestamps or total_candle_count == 0:
            return {
                "signals_per_day": 0.0,
                "signals_per_hour": 0.0,
                "clustering_factor": 0.0,
                "total_signals": 0,
            }

        total_days = max(1.0, (total_candle_count * candle_minutes) / 1440.0)
        total_hours = max(1.0, (total_candle_count * candle_minutes) / 60.0)
        
        # Calculate adjacent clustering: consecutive signals within 2 bars
        clustering_count = 0
        sorted_ts = sorted(signal_timestamps)
        threshold_ms = candle_minutes * 60 * 1000 * 2

        for i in range(1, len(sorted_ts)):
            if (sorted_ts[i] - sorted_ts[i - 1]) <= threshold_ms:
                clustering_count += 1

        clustering_factor = (clustering_count / len(sorted_ts)) if sorted_ts else 0.0

        return {
            "signals_per_day": round(len(signal_timestamps) / total_days, 2),
            "signals_per_hour": round(len(signal_timestamps) / total_hours, 3),
            "clustering_factor": round(clustering_factor, 3),
            "total_signals": len(signal_timestamps),
        }
