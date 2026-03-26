from __future__ import annotations

from typing import Any

from app.strategies.base import Strategy
from app.strategies.breakout import BreakoutStrategy
from app.strategies.ema_crossover import EmaCrossoverStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.regime_filter import RegimeFilterStrategy
from app.strategies.volatility_breakout import VolatilityBreakoutStrategy


STRATEGY_BUILDERS = {
    "ema_crossover": EmaCrossoverStrategy,
    "mean_reversion": MeanReversionStrategy,
    "breakout": BreakoutStrategy,
    "volatility_breakout": VolatilityBreakoutStrategy,
    "regime_filter": RegimeFilterStrategy,
}


def build_strategy(name: str, **kwargs: Any) -> Strategy:
    if name not in STRATEGY_BUILDERS:
        raise ValueError(f"Unsupported strategy: {name}")
    return STRATEGY_BUILDERS[name](**kwargs)
