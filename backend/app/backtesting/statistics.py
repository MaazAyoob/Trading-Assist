"""
Parametric and non-parametric statistical metrics calculator with deterministic bootstrap resampling.
Strictly distinguishes normal theory confidence intervals from empirical bootstrap intervals.
"""

import numpy as np
from typing import List, Optional, Tuple
from app.backtesting.models import DistributionStats


class StatisticalEngine:
    """
    Computes summary metrics, normal-theory confidence intervals,
    and deterministic bootstrap confidence intervals for analytical outcome distributions.
    """

    @staticmethod
    def compute_block_bootstrap(
        values: List[float],
        block_length: int = 5,
        bootstrap_iterations: int = 1000,
        confidence_level: float = 0.95,
        bootstrap_seed: int = 42,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Computes empirical mean confidence intervals via Moving Block Bootstrap (MBB).
        Preserves local time-series dependence and signal autocorrelation structure.
        """
        clean = [float(v) for v in values if v is not None and not np.isnan(v)]
        n = len(clean)
        if n < 10:
            return None, None

        b = max(1, min(block_length, n))
        arr = np.array(clean, dtype=np.float64)

        # Construct contiguous overlapping blocks
        num_blocks = n - b + 1
        blocks = [arr[i : i + b] for i in range(num_blocks)]
        blocks_arr = np.array(blocks)  # shape (num_blocks, b)

        num_blocks_needed = int(np.ceil(n / b))
        rng = np.random.default_rng(bootstrap_seed)

        # Resample blocks with replacement
        resampled_indices = rng.integers(0, num_blocks, size=(bootstrap_iterations, num_blocks_needed))
        resamples = blocks_arr[resampled_indices].reshape(bootstrap_iterations, -1)[:, :n]

        boot_means = np.mean(resamples, axis=1)
        alpha = 1.0 - confidence_level
        lower_pct = (alpha / 2.0) * 100.0
        upper_pct = (1.0 - (alpha / 2.0)) * 100.0

        lower_ci = float(np.percentile(boot_means, lower_pct))
        upper_ci = float(np.percentile(boot_means, upper_pct))
        return round(lower_ci, 6), round(upper_ci, 6)

    @staticmethod
    def compute_distribution_stats(
        values: List[float],
        confidence_level: float = 0.95,
        bootstrap_seed: int = 42,
        bootstrap_iterations: int = 1000,
        block_bootstrap_length: int = 5,
        min_sample_size: int = 10,
        compute_bootstrap: bool = True,
    ) -> DistributionStats:
        """
        Computes sample statistics, percentiles, normal theory CI, and bootstrap CI.
        """
        clean_values = [float(v) for v in values if v is not None and not np.isnan(v)]
        n = len(clean_values)

        if n == 0:
            return DistributionStats(sample_count=0, status="EMPTY", sample_warning="INSUFFICIENT_SAMPLE")

        arr = np.array(clean_values, dtype=np.float64)
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))

        p5_val = float(np.percentile(arr, 5))
        p25_val = float(np.percentile(arr, 25))
        p50_val = median_val
        p75_val = float(np.percentile(arr, 75))
        p95_val = float(np.percentile(arr, 95))

        if n < min_sample_size:
            return DistributionStats(
                sample_count=n,
                mean=round(mean_val, 6),
                median=round(median_val, 6),
                std_dev=round(float(np.std(arr, ddof=1)), 6) if n > 1 else None,
                std_error=None,
                ci_lower_normal=None,
                ci_upper_normal=None,
                bootstrap_mean_ci_lower=None,
                bootstrap_mean_ci_upper=None,
                bootstrap_median_ci_lower=None,
                bootstrap_median_ci_upper=None,
                block_bootstrap_mean_ci_lower=None,
                block_bootstrap_mean_ci_upper=None,
                p5=round(p5_val, 6),
                p25=round(p25_val, 6),
                p50=round(p50_val, 6),
                p75=round(p75_val, 6),
                p95=round(p95_val, 6),
                status="INSUFFICIENT_SAMPLE",
                sample_warning="INSUFFICIENT_SAMPLE",
            )

        std_dev_val = float(np.std(arr, ddof=1))
        std_error_val = float(std_dev_val / np.sqrt(n))

        # Normal Theory Confidence Interval (Critical Z approx for specified confidence)
        if abs(confidence_level - 0.95) < 0.01:
            z_crit = 1.959964
        elif abs(confidence_level - 0.90) < 0.01:
            z_crit = 1.644854
        elif abs(confidence_level - 0.99) < 0.01:
            z_crit = 2.575829
        else:
            z_crit = 1.959964

        ci_lower_norm = mean_val - (z_crit * std_error_val)
        ci_upper_norm = mean_val + (z_crit * std_error_val)

        # Bootstrap Resampling (only if requested)
        boot_mean_lower = boot_mean_upper = None
        boot_median_lower = boot_median_upper = None
        bb_lower = bb_upper = None

        if compute_bootstrap and n >= min_sample_size:
            rng = np.random.default_rng(bootstrap_seed)
            # Subsample for bootstrap if sample is extremely large (> 2500) to keep execution instant
            n_boot = min(n, 2500)
            boot_sample = rng.choice(arr, size=n_boot, replace=False) if n > 2500 else arr
            resamples = rng.choice(boot_sample, size=(bootstrap_iterations, n_boot), replace=True)

            boot_means = np.mean(resamples, axis=1)
            boot_medians = np.median(resamples, axis=1)

            alpha = 1.0 - confidence_level
            lower_pct = (alpha / 2.0) * 100.0
            upper_pct = (1.0 - (alpha / 2.0)) * 100.0

            boot_mean_lower = round(float(np.percentile(boot_means, lower_pct)), 6)
            boot_mean_upper = round(float(np.percentile(boot_means, upper_pct)), 6)
            boot_median_lower = round(float(np.percentile(boot_medians, lower_pct)), 6)
            boot_median_upper = round(float(np.percentile(boot_medians, upper_pct)), 6)

            bb_l, bb_u = StatisticalEngine.compute_block_bootstrap(
                values=clean_values[:n_boot] if n > 2500 else clean_values,
                block_length=block_bootstrap_length,
                bootstrap_iterations=bootstrap_iterations,
                confidence_level=confidence_level,
                bootstrap_seed=bootstrap_seed,
            )
            bb_lower, bb_upper = bb_l, bb_u

        sample_warning = "SMALL_SAMPLE" if n < 30 else "VALID"

        return DistributionStats(
            sample_count=n,
            mean=round(mean_val, 6),
            median=round(median_val, 6),
            std_dev=round(std_dev_val, 6),
            std_error=round(std_error_val, 6),
            ci_lower_normal=round(ci_lower_norm, 6),
            ci_upper_normal=round(ci_upper_norm, 6),
            bootstrap_mean_ci_lower=boot_mean_lower,
            bootstrap_mean_ci_upper=boot_mean_upper,
            bootstrap_median_ci_lower=boot_median_lower,
            bootstrap_median_ci_upper=boot_median_upper,
            block_bootstrap_mean_ci_lower=bb_lower,
            block_bootstrap_mean_ci_upper=bb_upper,
            p5=round(p5_val, 6),
            p25=round(p25_val, 6),
            p50=round(p50_val, 6),
            p75=round(p75_val, 6),
            p95=round(p95_val, 6),
            status="VALID",
            sample_warning=sample_warning,
        )
