from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import atr


class VolatilityBreakoutStrategy(Strategy):
    name = "volatility_breakout"
    description_ru = "Пробой волатильности: вход при импульсе выше ATR-порога, выход при затухании."

    def __init__(self, atr_period: int = 14, breakout_mult: float = 1.2, exit_mult: float = 0.7) -> None:
        self.atr_period = atr_period
        self.breakout_mult = breakout_mult
        self.exit_mult = exit_mult

    def parameter_space(self) -> dict[str, list[float | int]]:
        return {"atr_period": [10, 14, 20], "breakout_mult": [1.0, 1.2, 1.5], "exit_mult": [0.5, 0.7, 0.9]}

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))
        if len(candles) < self.atr_period + 3:
            return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        closes = [c.close for c in candles]
        atr_value = atr(highs, lows, closes, self.atr_period)
        if atr_value is None:
            return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="atr_unavailable")

        prev_close = closes[-2]
        last_close = closes[-1]
        move = last_close - prev_close
        if move > atr_value * self.breakout_mult and not context.has_position:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="buy",
                signal_type="entry",
                confidence=0.62,
                stop_loss=last_close - 1.5 * atr_value,
                take_profit=last_close + 2.0 * atr_value,
                reason="volatility_expansion",
                explanation="Импульс вверх превысил заданный ATR-порог; вход в трендовый импульс.",
            )
        if context.has_position and move < atr_value * self.exit_mult * -1:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="sell",
                signal_type="exit",
                confidence=0.6,
                reason="volatility_reversal",
                explanation="Обратный импульс против позиции: выход по защите капитала.",
            )
        return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="no_signal")
