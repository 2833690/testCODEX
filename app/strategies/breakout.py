from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import atr


class BreakoutStrategy(Strategy):
    name = "breakout"

    def __init__(self, lookback: int = 20, atr_period: int = 14, min_atr_pct: float = 0.003) -> None:
        self.lookback = lookback
        self.atr_period = atr_period
        self.min_atr_pct = min_atr_pct

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))
        if len(candles) < self.lookback + 1:
            return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")

        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        closes = [c.close for c in candles]
        last_price = closes[-1]
        rolling_high = max(highs[-self.lookback - 1 : -1])
        rolling_low = min(lows[-self.lookback - 1 : -1])
        atr_value = atr(highs, lows, closes, self.atr_period)
        if atr_value is None:
            return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_atr")
        if atr_value / last_price < self.min_atr_pct:
            return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="volatility_too_low")

        if last_price > rolling_high and not context.has_position:
            return StrategySignal(symbol=symbol, side="buy", signal_type="entry", confidence=0.65, stop_loss=last_price - (1.5 * atr_value), reason="upside_breakout")
        if last_price < rolling_low and context.has_position:
            return StrategySignal(symbol=symbol, side="sell", signal_type="exit", confidence=0.65, reason="downside_breakout")
        return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="no_breakout")
