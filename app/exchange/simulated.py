from __future__ import annotations

import csv
from pathlib import Path

from app.exchange.base import ExchangeAdapter
from app.models.market import Candle, MarketSnapshot
from app.models.trading import OrderRequest, OrderResult


class SimulatedExchangeAdapter(ExchangeAdapter):
    def __init__(self, csv_path: str = "data/sample_ohlcv.csv", symbol: str = "BTC/USDT") -> None:
        self.symbol = symbol
        self._candles = self._load_csv(csv_path)
        self._cursor = min(20, len(self._candles))

    def _load_csv(self, path: str) -> list[Candle]:
        rows: list[Candle] = []
        with Path(path).open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(
                    Candle(
                        timestamp=int(r["timestamp"]),
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        volume=float(r["volume"]),
                    )
                )
        return rows

    def step(self) -> None:
        if self._cursor < len(self._candles):
            self._cursor += 1

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        _ = timeframe
        if symbol != self.symbol:
            raise ValueError("Unsupported symbol for simulated adapter")
        start = max(0, self._cursor - limit)
        return self._candles[start : self._cursor]

    def fetch_ticker(self, symbol: str) -> MarketSnapshot:
        if symbol != self.symbol:
            raise ValueError("Unsupported symbol for simulated adapter")
        last = self._candles[self._cursor - 1].close
        return MarketSnapshot(symbol=symbol, bid=last * 0.9999, ask=last * 1.0001, last=last)

    def fetch_balance(self) -> dict[str, float]:
        return {"USDT": 10_000.0}

    def create_order(self, request: OrderRequest) -> OrderResult:
        raise NotImplementedError("Use paper broker for order simulation")

    def fetch_order(self, order_id: str, symbol: str) -> OrderResult:
        raise NotImplementedError
