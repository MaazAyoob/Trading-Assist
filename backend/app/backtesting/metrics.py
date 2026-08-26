from datetime import datetime, timezone
from typing import List, Dict, Tuple
from app.backtesting.models import (
    SignalOutcome,
    BacktestMetrics,
    HorizonMetrics,
    ConditionalBreakdown,
    OutcomeClassificationEnum,
)
from app.backtesting.config import BacktestConfig
from app.backtesting.statistics import StatisticalEngine


class MetricsAggregator:
    """
    Aggregates individual SignalOutcome records into comprehensive BacktestMetrics.
    """

    @classmethod
    def aggregate(
        cls,
        signal_outcomes: List[SignalOutcome],
        config: BacktestConfig,
        total_candles: int,
        start_timestamp: int,
        end_timestamp: int,
        wait_signal_count: int = 0,
        neutral_signal_count: int = 0,
    ) -> BacktestMetrics:
        """
        Builds BacktestMetrics from signal outcome records.
        """
        long_outcomes = [s for s in signal_outcomes if s.signal_direction == "LONG_SETUP"]
        short_outcomes = [s for s in signal_outcomes if s.signal_direction == "SHORT_SETUP"]

        total_signals = len(signal_outcomes)
        long_signals = len(long_outcomes)
        short_signals = len(short_outcomes)

        # Calculate time span in days
        time_span_ms = max(1, end_timestamp - start_timestamp)
        days = max(1.0 / 24.0, time_span_ms / (1000.0 * 86400.0))

        signals_per_day = round(total_signals / days, 3)
        signals_per_week = round(signals_per_day * 7.0, 3)
        signals_per_month = round(signals_per_day * 30.4375, 3)

        # 1. Horizon Metrics (Combined)
        horizon_metrics = cls._build_horizon_metrics(signal_outcomes, config)

        # 2. Directional Symmetry (Long vs Short)
        long_horizon_metrics = cls._build_horizon_metrics(long_outcomes, config)
        short_horizon_metrics = cls._build_horizon_metrics(short_outcomes, config)

        # 3. Conditional Breakdowns
        regime_breakdown = cls._build_conditional_slices(
            signal_outcomes,
            category="REGIME",
            key_getter=lambda s: s.regime_at_signal or "UNKNOWN",
            config=config,
        )

        strength_breakdown = cls._build_conditional_slices(
            signal_outcomes,
            category="STRENGTH",
            key_getter=lambda s: s.signal_strength or "UNKNOWN",
            config=config,
        )

        score_breakdown = cls._build_score_bucket_slices(signal_outcomes, config)

        volatility_breakdown = cls._build_conditional_slices(
            signal_outcomes,
            category="VOLATILITY",
            key_getter=lambda s: s.volatility_at_signal or "UNKNOWN",
            config=config,
        )

        structure_breakdown = cls._build_conditional_slices(
            signal_outcomes,
            category="STRUCTURE",
            key_getter=lambda s: s.structure_at_signal or "UNKNOWN",
            config=config,
        )

        def _get_quarter(s: SignalOutcome) -> str:
            dt = datetime.fromtimestamp(s.signal_timestamp / 1000.0, tz=timezone.utc)
            q = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{q}"

        subperiod_breakdown = cls._build_conditional_slices(
            signal_outcomes,
            category="SUBPERIOD",
            key_getter=_get_quarter,
            config=config,
        )

        return BacktestMetrics(
            total_candles=total_candles,
            total_signals=total_signals,
            long_signals=long_signals,
            short_signals=short_signals,
            wait_signals=wait_signal_count,
            neutral_signals=neutral_signal_count,
            signals_per_day=signals_per_day,
            signals_per_week=signals_per_week,
            signals_per_month=signals_per_month,
            horizon_metrics=horizon_metrics,
            long_horizon_metrics=long_horizon_metrics,
            short_horizon_metrics=short_horizon_metrics,
            regime_breakdown=regime_breakdown,
            strength_breakdown=strength_breakdown,
            score_breakdown=score_breakdown,
            volatility_breakdown=volatility_breakdown,
            structure_breakdown=structure_breakdown,
            subperiod_breakdown=subperiod_breakdown,
        )

    @classmethod
    def _build_horizon_metrics(
        cls,
        signals: List[SignalOutcome],
        config: BacktestConfig,
        compute_bootstrap: bool = True,
    ) -> Dict[int, HorizonMetrics]:
        """
        Aggregates distribution statistics for each configured horizon.
        """
        metrics: Dict[int, HorizonMetrics] = {}

        for h in config.horizons:
            fwd_returns: List[float] = []
            mfes: List[float] = []
            maes: List[float] = []
            pos_count = 0
            neg_count = 0
            flat_count = 0
            insufficient_count = 0

            for s in signals:
                outcome = s.outcomes.get(h, None)
                if not outcome or outcome.status == OutcomeClassificationEnum.INSUFFICIENT_HORIZON:
                    insufficient_count += 1
                    continue

                if outcome.forward_return is not None:
                    # If cost model is enabled, use net forward return
                    val = outcome.estimated_net_forward_return if (config.cost_model.enabled and outcome.estimated_net_forward_return is not None) else outcome.forward_return
                    fwd_returns.append(val)

                if outcome.mfe is not None:
                    mfes.append(outcome.mfe)
                if outcome.mae is not None:
                    maes.append(outcome.mae)

                if outcome.status == OutcomeClassificationEnum.POSITIVE_FORWARD_RETURN:
                    pos_count += 1
                elif outcome.status == OutcomeClassificationEnum.NEGATIVE_FORWARD_RETURN:
                    neg_count += 1
                elif outcome.status == OutcomeClassificationEnum.FLAT_FORWARD_RETURN:
                    flat_count += 1

            valid_count = len(fwd_returns)
            pos_ratio = round(pos_count / valid_count, 4) if valid_count > 0 else 0.0

            fwd_stats = StatisticalEngine.compute_distribution_stats(
                fwd_returns,
                confidence_level=config.confidence_level,
                bootstrap_seed=config.bootstrap_seed,
                bootstrap_iterations=config.bootstrap_iterations,
                block_bootstrap_length=config.block_bootstrap_length,
                min_sample_size=config.min_sample_size,
                compute_bootstrap=compute_bootstrap,
            )

            mfe_stats = StatisticalEngine.compute_distribution_stats(
                mfes,
                confidence_level=config.confidence_level,
                bootstrap_seed=config.bootstrap_seed,
                bootstrap_iterations=config.bootstrap_iterations,
                block_bootstrap_length=config.block_bootstrap_length,
                min_sample_size=config.min_sample_size,
                compute_bootstrap=compute_bootstrap,
            )

            mae_stats = StatisticalEngine.compute_distribution_stats(
                maes,
                confidence_level=config.confidence_level,
                bootstrap_seed=config.bootstrap_seed,
                bootstrap_iterations=config.bootstrap_iterations,
                block_bootstrap_length=config.block_bootstrap_length,
                min_sample_size=config.min_sample_size,
                compute_bootstrap=compute_bootstrap,
            )

            metrics[h] = HorizonMetrics(
                horizon=h,
                forward_return_stats=fwd_stats,
                mfe_stats=mfe_stats,
                mae_stats=mae_stats,
                positive_count=pos_count,
                negative_count=neg_count,
                flat_count=flat_count,
                insufficient_horizon_count=insufficient_count,
                positive_ratio=pos_ratio,
            )

        return metrics

    @classmethod
    def _build_conditional_slices(
        cls,
        signals: List[SignalOutcome],
        category: str,
        key_getter,
        config: BacktestConfig,
    ) -> Dict[str, ConditionalBreakdown]:
        """
        Groups signals by arbitrary key and computes horizon metrics per group.
        """
        grouped: Dict[str, List[SignalOutcome]] = {}
        for s in signals:
            key = key_getter(s)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(s)

        breakdowns: Dict[str, ConditionalBreakdown] = {}
        for key, group_signals in grouped.items():
            hm = cls._build_horizon_metrics(group_signals, config, compute_bootstrap=False)
            breakdowns[key] = ConditionalBreakdown(
                category=category,
                key=key,
                sample_count=len(group_signals),
                horizon_metrics=hm,
            )
        return breakdowns

    @classmethod
    def _build_score_bucket_slices(
        cls,
        signals: List[SignalOutcome],
        config: BacktestConfig,
    ) -> Dict[str, ConditionalBreakdown]:
        """
        Buckets signals into explicit positive and negative score bands.
        """
        all_buckets = config.score_buckets_positive + config.score_buckets_negative
        bucket_signals: Dict[str, List[SignalOutcome]] = {}

        for low, high in all_buckets:
            label = f"{int(low)} to {int(high)}"
            bucket_signals[label] = []

        for s in signals:
            score = s.signal_score
            for low, high in all_buckets:
                if low <= score < high or (high == 100.0 and score == 100.0) or (low == -100.0 and score == -100.0):
                    label = f"{int(low)} to {int(high)}"
                    bucket_signals[label].append(s)
                    break

        breakdowns: Dict[str, ConditionalBreakdown] = {}
        for label, group_signals in bucket_signals.items():
            if len(group_signals) > 0:
                hm = cls._build_horizon_metrics(group_signals, config, compute_bootstrap=False)
                breakdowns[label] = ConditionalBreakdown(
                    category="SCORE_RANGE",
                    key=label,
                    sample_count=len(group_signals),
                    horizon_metrics=hm,
                )
        return breakdowns
