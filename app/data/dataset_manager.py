from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.data.validation import validate_symbol
from app.exchange.base import ExchangeAdapter


@dataclass
class DatasetRef:
    symbol: str
    timeframe: str
    version: int
    path: Path


class DatasetManager:
    def __init__(self, datasets_dir: str = "storage/datasets") -> None:
        self.datasets_dir = Path(datasets_dir)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.datasets_dir / "metadata.json"
        if not self.metadata_path.exists():
            self.metadata_path.write_text(json.dumps({"datasets": {}}, ensure_ascii=False, indent=2))

    def _meta(self) -> dict:
        return json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def _save_meta(self, meta: dict) -> None:
        self.metadata_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        validate_symbol(symbol)
        return symbol.replace("-", "/").upper()

    @staticmethod
    def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        cols = ["timestamp", "open", "high", "low", "close", "volume"]
        frame = df.copy()
        frame.columns = [c.lower() for c in frame.columns]
        return frame[cols].dropna().drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

    def import_csv(self, csv_path: str, symbol: str, timeframe: str) -> DatasetRef:
        frame = pd.read_csv(csv_path)
        return self._save_dataset(self.clean_ohlcv(frame), self.normalize_symbol(symbol), timeframe, source="csv_import")

    def update_from_exchange(self, exchange: ExchangeAdapter, symbol: str, timeframe: str, limit: int = 1000) -> DatasetRef:
        normalized = self.normalize_symbol(symbol)
        candles = exchange.fetch_ohlcv(normalized, timeframe, limit=limit)
        frame = pd.DataFrame([c.__dict__ for c in candles])
        return self._save_dataset(self.clean_ohlcv(frame), normalized, timeframe, source="exchange_update")

    def _read_dataset(self, ref: DatasetRef) -> pd.DataFrame:
        if ref.path.suffix == ".parquet":
            return pd.read_parquet(ref.path)
        return pd.read_csv(ref.path)

    def resample(self, dataset: DatasetRef, timeframe: str) -> DatasetRef:
        frame = self._read_dataset(dataset)
        ts = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame = frame.set_index(ts)
        rule = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1d"}.get(timeframe, "5min")
        resampled = frame.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
        out = resampled.reset_index(drop=True)
        out["timestamp"] = (resampled.index.astype("int64") // 10**6).values
        return self._save_dataset(out[["timestamp", "open", "high", "low", "close", "volume"]], dataset.symbol, timeframe, source="resample")

    def _save_dataset(self, frame: pd.DataFrame, symbol: str, timeframe: str, source: str) -> DatasetRef:
        meta = self._meta()
        key = f"{symbol}:{timeframe}"
        version = int(meta["datasets"].get(key, {}).get("latest_version", 0)) + 1
        symbol_dir = self.datasets_dir / symbol.replace("/", "_")
        symbol_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = symbol_dir / f"{timeframe}_v{version}.parquet"
        csv_path = symbol_dir / f"{timeframe}_v{version}.csv"
        path = parquet_path
        try:
            frame.to_parquet(parquet_path, index=False)
        except Exception:
            frame.to_csv(csv_path, index=False)
            path = csv_path

        meta["datasets"][key] = {
            "latest_version": version,
            "path": str(path),
            "rows": len(frame),
            "source": source,
        }
        self._save_meta(meta)
        return DatasetRef(symbol=symbol, timeframe=timeframe, version=version, path=path)
