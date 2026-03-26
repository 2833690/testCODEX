from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal


class Strategy(ABC):
    name: str
    description_ru: str = ""

    @abstractmethod
    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        raise NotImplementedError

    def parameter_space(self) -> dict[str, list[Any]]:
        return {}

    def config(self) -> dict[str, Any]:
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}
