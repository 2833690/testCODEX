from pathlib import Path

import pandas as pd

from app.data.dataset_manager import DatasetManager


def test_import_csv_and_resample(tmp_path: Path) -> None:
    manager = DatasetManager(str(tmp_path / "datasets"))
    source = tmp_path / "ohlcv.csv"
    df = pd.DataFrame(
        {
            "timestamp": [1, 2, 3, 4, 5],
            "open": [1, 1, 1, 1, 1],
            "high": [2, 2, 2, 2, 2],
            "low": [0.5, 0.5, 0.5, 0.5, 0.5],
            "close": [1, 1.1, 1.2, 1.3, 1.4],
            "volume": [10, 11, 12, 13, 14],
        }
    )
    df.to_csv(source, index=False)
    ref = manager.import_csv(str(source), "btc/usdt", "1m")
    assert ref.path.exists()
    ref2 = manager.resample(ref, "5m")
    assert ref2.path.exists()
