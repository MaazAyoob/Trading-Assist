import os
import json
import pytest
from app.data.schema import Candle, CandleStateEnum
from app.backtesting.dataset import DatasetManager
from app.backtesting.models import DatasetMetadata


def test_dataset_hash_determinism_and_sensitivity():
    candles = [
        Candle(
            timestamp=1700000000000 + i * 900000,
            open=50000.0 + i,
            high=50100.0 + i,
            low=49900.0 + i,
            close=50050.0 + i,
            volume=100.0,
            close_time=1700000000000 + (i + 1) * 900000 - 1,
            is_closed=True,
            state=CandleStateEnum.CLOSED,
        )
        for i in range(50)
    ]

    hash1 = DatasetManager.compute_dataset_hash(candles)
    hash2 = DatasetManager.compute_dataset_hash(candles)
    assert hash1 == hash2

    # Mutate one close price slightly
    mutated_candles = [c.model_copy() for c in candles]
    mutated_candles[10].close += 0.01
    hash_mutated = DatasetManager.compute_dataset_hash(mutated_candles)
    assert hash1 != hash_mutated


def test_dataset_manager_raw_file_loading_and_saving(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    raw_payload = {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "start_timestamp": 1700000000000,
        "end_timestamp": 1700000000000 + 10 * 900000,
        "download_timestamp": 1700000000000,
        "klines": [
            [
                1700000000000 + i * 900000,
                "50000.0",
                "50100.0",
                "49900.0",
                "50050.0",
                "100.0",
                1700000000000 + (i + 1) * 900000 - 1,
                "5005000.0",
                500,
            ]
            for i in range(10)
        ],
    }

    raw_file = raw_dir / "BTCUSDT_15m_test.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f)

    dm = DatasetManager(raw_data_dir=str(raw_dir), processed_data_dir=str(processed_dir))
    candles, metadata = dm.load_from_raw_file(str(raw_file))

    assert len(candles) == 10
    assert metadata.symbol == "BTCUSDT"
    assert metadata.timeframe == "15m"
    assert metadata.candle_count == 10
    assert len(metadata.sha256_hash) == 64

    # Save to processed
    processed_path = dm.save_processed_dataset(candles, metadata)
    assert os.path.exists(processed_path)

    # Load back
    loaded_candles, loaded_meta = dm.load_processed_dataset(metadata.dataset_id)
    assert len(loaded_candles) == 10
    assert loaded_meta.sha256_hash == metadata.sha256_hash
