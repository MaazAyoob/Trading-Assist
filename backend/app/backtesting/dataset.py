"""
Historical dataset management and validation for backtesting.
Guarantees immutability of raw files and produces verifiable DatasetMetadata with SHA-256 integrity hash.
"""

import os
import json
import hashlib
import time
from typing import List, Tuple, Optional, Dict, Any
from app.data.schema import Candle, CandleStateEnum
from app.data.quality import MarketDataQualityValidator
from app.backtesting.models import DatasetMetadata
from app.core.timeframes import SUPPORTED_TIMEFRAMES
from app.core.logging import logger


class DatasetManager:
    """
    Manages raw download ingestion, data quality validation,
    cryptographic hashing, and processed dataset persistence.
    """

    def __init__(self, raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed"):
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)

    @staticmethod
    def compute_dataset_hash(candles: List[Candle]) -> str:
        """
        Computes a deterministic SHA-256 hash across the canonical sequence of OHLCV candles.
        """
        hasher = hashlib.sha256()
        for c in candles:
            # Canonical representation: timestamp|open|high|low|close|volume
            record = f"{c.timestamp}:{c.open:.8f}:{c.high:.8f}:{c.low:.8f}:{c.close:.8f}:{c.volume:.8f}\n"
            hasher.update(record.encode("utf-8"))
        return hasher.hexdigest()

    def parse_binance_raw_klines(self, raw_klines: List[List[Any]]) -> List[Candle]:
        """
        Parses Binance raw kline arrays into strictly confirmed CLOSED Candle domain objects.
        """
        candles: List[Candle] = []
        for k in raw_klines:
            candles.append(
                Candle(
                    timestamp=int(k[0]),
                    open=float(k[1]),
                    high=float(k[2]),
                    low=float(k[3]),
                    close=float(k[4]),
                    volume=float(k[5]),
                    close_time=int(k[6]),
                    quote_volume=float(k[7]) if len(k) > 7 else None,
                    trades_count=int(k[8]) if len(k) > 8 else None,
                    is_closed=True,
                    state=CandleStateEnum.CLOSED,
                )
            )
        return candles

    def load_from_raw_file(self, raw_filepath: str) -> Tuple[List[Candle], DatasetMetadata]:
        """
        Loads and parses a raw JSON kline file, validates data quality,
        and constructs DatasetMetadata without modifying the raw file.
        """
        with open(raw_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        symbol = data["symbol"]
        timeframe = data["timeframe"]
        raw_klines = data.get("klines", [])

        candles = self.parse_binance_raw_klines(raw_klines)
        _, quality = MarketDataQualityValidator.validate_dataset(candles, timeframe=timeframe, symbol=symbol)

        sha256 = self.compute_dataset_hash(candles)
        start_ts = candles[0].timestamp if candles else 0
        end_ts = candles[-1].close_time if candles and candles[-1].close_time else (candles[-1].timestamp if candles else 0)

        dataset_id = f"{symbol}_{timeframe}_{start_ts}_{end_ts}_{sha256[:8]}"

        gap_records = [
            GapRecord(
                gap_start=g["gap_start"],
                gap_end=g["gap_end"],
                missing_candle_count=g["missing_candle_count"],
            )
            for g in getattr(quality, "gaps", [])
        ]

        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            symbol=symbol,
            timeframe=timeframe,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            candle_count=len(candles),
            gap_count=quality.gap_count,
            duplicate_count=quality.duplicate_count,
            invalid_count=quality.invalid_count,
            dataset_version="v1.0",
            gaps=gap_records,
            sha256_hash=sha256,
            quality_status=quality.status.value,
            download_timestamp=data.get("download_timestamp", int(time.time() * 1000)),
            source="BINANCE_PUBLIC_REST",
        )

        return candles, metadata

    def save_processed_dataset(
        self,
        candles: List[Candle],
        metadata: DatasetMetadata,
        raw_filepath: Optional[str] = None,
    ) -> str:
        """
        Saves the processed dataset and metadata into data/processed/ and registers in manifest.
        """
        from app.backtesting.manifest import ManifestManager
        filepath = os.path.join(self.processed_data_dir, f"{metadata.dataset_id}.json")
        payload = {
            "metadata": metadata.model_dump(),
            "candles": [c.model_dump() for c in candles],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        abs_path = os.path.abspath(filepath)
        ManifestManager().register_dataset(metadata, raw_filepath=raw_filepath, processed_filepath=abs_path)
        return abs_path

    def load_processed_dataset(self, dataset_id: str) -> Tuple[List[Candle], DatasetMetadata]:
        """
        Loads a previously processed dataset from data/processed/.
        """
        filepath = os.path.join(self.processed_data_dir, f"{dataset_id}.json")
        if not os.path.exists(filepath):
            # Try direct path
            filepath = dataset_id

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Processed dataset not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = DatasetMetadata(**data["metadata"])
        candles = [Candle(**c) for c in data["candles"]]

        # Verify hash integrity
        recalculated_hash = self.compute_dataset_hash(candles)
        if recalculated_hash != metadata.sha256_hash:
            raise ValueError(f"Dataset corruption detected: SHA256 mismatch for {dataset_id}")

        return candles, metadata
