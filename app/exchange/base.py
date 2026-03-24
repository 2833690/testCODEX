from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.market import Candle, MarketSnapshot
from app.models.trading import OrderRequest, OrderResult


class ExchangeAdapter(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        raise NotImplementedError

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError

    @abstractmethod
    def fetch_balance(self) -> dict[str, float]:
        raise NotImplementedError

    @abstractmethod
    def create_order(self, request: OrderRequest) -> OrderResult:
        raise NotImplementedError

    @abstractmethod
    def fetch_order(self, order_id: str, symbol: str) -> OrderResult:
        raise NotImplementedError
