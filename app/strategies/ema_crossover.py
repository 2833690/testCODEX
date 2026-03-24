from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import ema


class EmaCrossoverStrategy(Strategy):
    name = "ema_crossover"

    def __init__(self, fast_period: int = 12, slow_period: int = 26) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        closes = [c.close for c in candles]
        fast = ema(closes, self.fast_period)
        slow = ema(closes, self.slow_period)
        symbol = "UNKNOWN" if not candles else context.metadata.get("symbol", "BTC/USDT")
        if fast is None or slow is None:
            return StrategySignal(symbol=str(symbol), side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")
        if fast > slow and not context.has_position:
            stop = closes[-1] * 0.99
            return StrategySignal(symbol=str(symbol), side="buy", signal_type="entry", confidence=0.6, stop_loss=stop, reason="fast_above_slow")
        if fast < slow and context.has_position:
            return StrategySignal(symbol=str(symbol), side="sell", signal_type="exit", confidence=0.6, reason="fast_below_slow")
        return StrategySignal(symbol=str(symbol), side="buy", signal_type="hold", confidence=0.0, reason="no_change")
