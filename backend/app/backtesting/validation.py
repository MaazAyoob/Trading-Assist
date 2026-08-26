"""
Chronological dataset partitioning and walk-forward evaluation architecture.
Guarantees zero future lookahead, zero candle shuffling, and strict out-of-sample isolation.
"""

from typing import List, Dict, Tuple, Optional
from app.data.schema import Candle
from app.backtesting.config import SplitConfig


class DatasetSplitter:
    """
    Partitions candle sequences chronologically into Train, Validation, and Test subsets.
    """

    @staticmethod
    def split_chronological(
        candles: List[Candle],
        split_config: SplitConfig,
    ) -> Dict[str, List[Candle]]:
        """
        Splits candles strictly along chronological index boundaries without shuffling.
        """
        n = len(candles)
        if n == 0:
            return {"TRAIN": [], "VALIDATION": [], "TEST": []}

        train_end = int(n * split_config.train_ratio)
        val_end = int(n * (split_config.train_ratio + split_config.validation_ratio))

        # Ensure bounds
        train_end = max(1, min(train_end, n - 2)) if n >= 3 else n
        val_end = max(train_end + 1, min(val_end, n - 1)) if n >= 3 else n

        train_set = candles[:train_end]
        val_set = candles[train_end:val_end]
        test_set = candles[val_end:]

        return {
            "TRAIN": train_set,
            "VALIDATION": val_set,
            "TEST": test_set,
        }


class WalkForwardWindow:
    """
    Representation of a single walk-forward chronological evaluation fold.
    """
    def __init__(
        self,
        fold_index: int,
        train_candles: List[Candle],
        val_candles: List[Candle],
        test_candles: List[Candle],
    ):
        self.fold_index = fold_index
        self.train_candles = train_candles
        self.val_candles = val_candles
        self.test_candles = test_candles


class WalkForwardManager:
    """
    Generates chronological walk-forward rolling windows for out-of-sample evaluation.
    Zero automated parameter optimization is performed in Phase 6.
    """

    @staticmethod
    def generate_expanding_windows(
        candles: List[Candle],
        initial_train_bars: int = 500,
        test_bars: int = 100,
        val_bars: int = 50,
    ) -> List[WalkForwardWindow]:
        """
        Constructs expanding-window walk-forward folds.
        """
        n = len(candles)
        folds: List[WalkForwardWindow] = []
        curr_train_end = initial_train_bars
        fold_idx = 0

        while curr_train_end + val_bars + test_bars <= n:
            val_end = curr_train_end + val_bars
            test_end = val_end + test_bars

            train_slice = candles[:curr_train_end]
            val_slice = candles[curr_train_end:val_end]
            test_slice = candles[val_end:test_end]

            folds.append(
                WalkForwardWindow(
                    fold_index=fold_idx,
                    train_candles=train_slice,
                    val_candles=val_slice,
                    test_candles=test_slice,
                )
            )

            # Advance window
            curr_train_end += test_bars
            fold_idx += 1

        return folds
