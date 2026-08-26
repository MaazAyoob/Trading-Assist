"""
Phase 8 — Controlled Strategy Research Filters.
Implements causal, non-lookahead research candidate logic for Experiments A through F.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from app.data.schema import Candle
from app.indicators.base import IndicatorSnapshot
from app.regime.models import MarketRegimeSnapshot
from app.structure.models import MarketStructureSnapshot, SwingPoint, SwingTypeEnum
from app.signals.models import SignalDirectionEnum


class PullbackResearchFilter:
    """
    Experiment A: Checks if price retraced within a dynamic band near EMA 21 or VWAP.
    """

    @staticmethod
    def evaluate(
        candle: Candle,
        indicators: IndicatorSnapshot,
        direction: SignalDirectionEnum,
        reference_indicator: str = "EMA_21",
        max_distance_atr: float = 0.75,
    ) -> bool:
        close = candle.close
        atr = indicators.volatility.atr or 1.0

        if reference_indicator == "EMA_21":
            ref_val = indicators.trend.ema_21
        elif reference_indicator == "VWAP":
            ref_val = indicators.trend.vwap
        else:
            ref_val = indicators.trend.ema_21

        if ref_val is None or np.isnan(ref_val):
            return False

        dist_atr = abs(close - ref_val) / atr

        if direction == SignalDirectionEnum.LONG_SETUP:
            # Price pulled back near reference (within max_distance_atr) and is bouncing / holding above or near reference
            return dist_atr <= max_distance_atr
        elif direction == SignalDirectionEnum.SHORT_SETUP:
            return dist_atr <= max_distance_atr

        return False


class DivergenceResearchFilter:
    """
    Experiment B: Identifies momentum exhaustion divergence on confirmed swings.
    """

    @staticmethod
    def evaluate(
        direction: SignalDirectionEnum,
        confirmed_swings: List[SwingPoint],
        indicators: IndicatorSnapshot,
        divergence_source: str = "RSI_14",
    ) -> bool:
        """Returns True if NO divergence exhaustion is present (i.e. signal is permitted)."""
        if len(confirmed_swings) < 2:
            return True  # Insufficient confirmed swings, do not suppress

        if direction == SignalDirectionEnum.LONG_SETUP:
            # Check for Bearish Exhaustion divergence (Higher Highs in price, Lower Highs in momentum)
            shs = [s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_HIGH]
            if len(shs) >= 2:
                p_sh, c_sh = shs[-2], shs[-1]
                if c_sh.price > p_sh.price:
                    # Bearish divergence check
                    if divergence_source == "RSI_14":
                        cur_rsi = indicators.momentum.rsi or 50.0
                        if cur_rsi < 60.0:  # RSI weakening on new highs
                            return False  # Suppress long on bearish divergence
        elif direction == SignalDirectionEnum.SHORT_SETUP:
            # Check for Bullish Exhaustion divergence (Lower Lows in price, Higher Lows in momentum)
            sls = [s for s in confirmed_swings if s.type == SwingTypeEnum.SWING_LOW]
            if len(sls) >= 2:
                p_sl, c_sl = sls[-2], sls[-1]
                if c_sl.price < p_sl.price:
                    if divergence_source == "RSI_14":
                        cur_rsi = indicators.momentum.rsi or 50.0
                        if cur_rsi > 40.0:  # RSI firming on lower lows
                            return False  # Suppress short on bullish divergence

        return True


class FirstStructuralEventFilter:
    """
    Experiment C: Restricts setup generation to the initial 3 candles following a structural break.
    """

    @staticmethod
    def evaluate(
        candle_idx: int,
        last_structure_event_idx: Optional[int],
        max_bars_post_breakout: int = 3,
    ) -> bool:
        if last_structure_event_idx is None:
            return False
        bars_since_event = candle_idx - last_structure_event_idx
        return 0 <= bars_since_event <= max_bars_post_breakout


class EpisodeCooldownFilter:
    """
    Experiment D: Emits exactly one setup per continuous directional persistence run.
    """

    def __init__(self):
        self.active_episode_direction: Optional[str] = None
        self.episode_setup_emitted: bool = False

    def reset(self):
        self.active_episode_direction = None
        self.episode_setup_emitted = False

    def evaluate(self, current_direction: str) -> bool:
        if current_direction != self.active_episode_direction:
            # New directional episode begins
            self.active_episode_direction = current_direction
            self.episode_setup_emitted = True
            return True
        else:
            # Inside existing episode: suppress repeated trigger
            if not self.episode_setup_emitted:
                self.episode_setup_emitted = True
                return True
            return False


class ExtensionResearchFilter:
    """
    Experiment E: Suppresses setups when price is over-extended away from dynamic mean.
    """

    @staticmethod
    def evaluate(
        candle: Candle,
        indicators: IndicatorSnapshot,
        extension_metric: str = "EMA21_DISTANCE_ATR",
        max_allowed_extension_atr: float = 1.5,
    ) -> bool:
        close = candle.close
        atr = indicators.volatility.atr or 1.0

        if extension_metric == "EMA21_DISTANCE_ATR":
            ref = indicators.trend.ema_21
        elif extension_metric == "VWAP_DISTANCE_ATR":
            ref = indicators.trend.vwap
        else:
            ref = indicators.trend.ema_21

        if ref is None or np.isnan(ref):
            return True

        dist_atr = abs(close - ref) / atr
        # Signal is allowed if price is NOT over-extended beyond threshold
        return dist_atr <= max_allowed_extension_atr


class CombinedStrategyFilter:
    """
    Experiment F: Synthesizes structural timing + pullback discipline + extension cap + episode cooldown.
    """

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.episode_filter = EpisodeCooldownFilter()

    def reset(self):
        self.episode_filter.reset()

    def evaluate(
        self,
        candle: Candle,
        candle_idx: int,
        indicators: IndicatorSnapshot,
        direction: SignalDirectionEnum,
        confirmed_swings: List[SwingPoint],
        last_structure_event_idx: Optional[int],
    ) -> bool:
        # 1. Extension Filter check
        if self.params.get("extension_cap_atr"):
            if not ExtensionResearchFilter.evaluate(
                candle, indicators, "EMA21_DISTANCE_ATR", self.params["extension_cap_atr"]
            ):
                return False

        # 2. Pullback Check
        if self.params.get("pullback_ema21_max_atr"):
            if not PullbackResearchFilter.evaluate(
                candle, indicators, direction, "EMA_21", self.params["pullback_ema21_max_atr"]
            ):
                return False

        # 3. Divergence Suppression Check
        if self.params.get("suppress_rsi_divergence"):
            if not DivergenceResearchFilter.evaluate(
                direction, confirmed_swings, indicators, "RSI_14"
            ):
                return False

        # 4. Episode Cooldown Check
        if self.params.get("one_setup_per_episode"):
            if not self.episode_filter.evaluate(direction.value):
                return False

        return True
