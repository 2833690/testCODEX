from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import ema


class RegimeFilterStrategy(Strategy):
    name = "regime_filter"
    description_ru = "Режимная стратегия: трендовый вход только в bull-режиме и защитный выход в bear/sideways."

    def __init__(self, fast_period: int = 20, slow_period: int = 50) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def parameter_space(self) -> dict[str, list[int]]:
        return {"fast_period": [10, 20, 30], "slow_period": [40, 50, 80]}

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))
        closes = [c.close for c in candles]
        fast = ema(closes, self.fast_period)
        slow = ema(closes, self.slow_period)
        if fast is None or slow is None:
            return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")

        if context.regime == "bull" and fast > slow and not context.has_position:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="buy",
                signal_type="entry",
                confidence=0.64,
                reason="bull_regime_trend",
                explanation="Режим bull + подтверждение EMA, разрешён вход в long.",
            )
        if context.has_position and context.regime in {"bear", "sideways"}:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="sell",
                signal_type="exit",
                confidence=0.58,
                reason="regime_exit",
                explanation="Неблагоприятный рыночный режим для удержания long-позиции.",
            )
        return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="filtered")
