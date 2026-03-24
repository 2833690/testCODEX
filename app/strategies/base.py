from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal


class Strategy(ABC):
    name: str

    @abstractmethod
    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        raise NotImplementedError
