from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.trading import OrderRequest, OrderResult


class LiveExecutionInterface(ABC):
    @abstractmethod
    def submit_order(self, order: OrderRequest, timeout_seconds: float) -> OrderResult:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch_order(self, order_id: str, symbol: str) -> OrderResult:
        raise NotImplementedError
