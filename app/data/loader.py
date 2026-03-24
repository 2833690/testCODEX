from __future__ import annotations

import json
from pathlib import Path

from app.data.validation import validate_symbol, validate_timeframe
from app.exchange.base import ExchangeAdapter
from app.models.market import Candle


class OhlcvLoader:
    def __init__(self, exchange: ExchangeAdapter, cache_dir: str = ".cache") -> None:
        self.exchange = exchange
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, symbol: str, timeframe: str, limit: int) -> Path:
        sanitized = symbol.replace("/", "_")
        return self.cache_dir / f"{sanitized}_{timeframe}_{limit}.json"

    def load(self, symbol: str, timeframe: str, limit: int = 500, use_cache: bool = True) -> list[Candle]:
        validate_symbol(symbol)
        validate_timeframe(timeframe)
        path = self._cache_path(symbol, timeframe, limit)
        if use_cache and path.exists():
            raw = json.loads(path.read_text())
            return [Candle(**item) for item in raw]

        candles = self.exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        path.write_text(json.dumps([c.__dict__ for c in candles]))
        return candles
