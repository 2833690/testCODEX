from __future__ import annotations

from app.exchange.base import ExchangeAdapter
from app.models.market import Candle


class CandleFeed:
    """Polling abstraction; websocket transport can be added behind this interface later."""

    def __init__(self, exchange: ExchangeAdapter, symbol: str, timeframe: str) -> None:
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe

    def latest(self, limit: int = 200) -> list[Candle]:
        return self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
