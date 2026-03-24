from __future__ import annotations

from app.strategies.base import Strategy
from app.strategies.breakout import BreakoutStrategy
from app.strategies.ema_crossover import EmaCrossoverStrategy
from app.strategies.mean_reversion import MeanReversionStrategy


def build_strategy(name: str) -> Strategy:
    strategies: dict[str, Strategy] = {
        "ema_crossover": EmaCrossoverStrategy(),
        "mean_reversion": MeanReversionStrategy(),
        "breakout": BreakoutStrategy(),
    }
    if name not in strategies:
        raise ValueError(f"Unsupported strategy: {name}")
    return strategies[name]
