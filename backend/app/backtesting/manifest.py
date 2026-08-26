"""
Dataset Manifest Management for Phase 6.1 Historical Datasets.
Tracks provenance, quality, gap lists, checksums, and metadata immutability.
"""

import os
import json
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.backtesting.models import DatasetMetadata, GapRecord
from app.core.logging import logger


class DatasetManifestRecord(BaseModel):
    dataset_id: str
    symbol: str
    timeframe: str
    start_timestamp: int
    end_timestamp: int
    candle_count: int
    gap_count: int = 0
    duplicate_count: int = 0
    invalid_count: int = 0
    dataset_version: str = "v1.0"
    gaps: List[GapRecord] = Field(default_factory=list)
    sha256_hash: str
    quality_status: str
    download_timestamp: int
    source: str = "BINANCE_PUBLIC_REST"
    raw_filepath: Optional[str] = None
    processed_filepath: Optional[str] = None


class ManifestManager:
    """
    Manages the global manifest file (data/manifest.json) recording all historical datasets.
    """

    def __init__(self, manifest_path: str = "data/manifest.json"):
        self.manifest_path = manifest_path
        os.makedirs(os.path.dirname(os.path.abspath(self.manifest_path)), exist_ok=True)

    def load_manifest(self) -> Dict[str, DatasetManifestRecord]:
        if not os.path.exists(self.manifest_path):
            return {}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: DatasetManifestRecord(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Failed to load dataset manifest from {self.manifest_path}: {e}")
            return {}

    def register_dataset(
        self,
        metadata: DatasetMetadata,
        raw_filepath: Optional[str] = None,
        processed_filepath: Optional[str] = None,
    ) -> DatasetManifestRecord:
        manifest = self.load_manifest()
        record = DatasetManifestRecord(
            dataset_id=metadata.dataset_id,
            symbol=metadata.symbol,
            timeframe=metadata.timeframe,
            start_timestamp=metadata.start_timestamp,
            end_timestamp=metadata.end_timestamp,
            candle_count=metadata.candle_count,
            gap_count=metadata.gap_count,
            duplicate_count=metadata.duplicate_count,
            invalid_count=metadata.invalid_count,
            dataset_version=metadata.dataset_version,
            gaps=metadata.gaps,
            sha256_hash=metadata.sha256_hash,
            quality_status=metadata.quality_status,
            download_timestamp=metadata.download_timestamp,
            source=metadata.source,
            raw_filepath=raw_filepath,
            processed_filepath=processed_filepath,
        )
        manifest[metadata.dataset_id] = record

        # Save manifest
        serializable = {k: v.model_dump() for k, v in manifest.items()}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)

        logger.info(f"Registered dataset {metadata.dataset_id} in manifest ({self.manifest_path})")
        return record
