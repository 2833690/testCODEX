from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import atr, rsi, sma, stddev


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def __init__(self, period: int = 20, rsi_period: int = 14, rsi_buy: float = 30.0, rsi_sell: float = 70.0) -> None:
        self.period = period
        self.rsi_period = rsi_period
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))

        mid = sma(closes, self.period)
        sd = stddev(closes, self.period)
        rv = rsi(closes, self.rsi_period)
        atr_value = atr(highs, lows, closes, 14)
        if mid is None or sd is None or rv is None:
            return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")

        lower = mid - 2 * sd
        upper = mid + 2 * sd
        price = closes[-1]
        band_distance = abs(price - mid) / mid if mid else 0.0
        confidence = min(0.9, 0.5 + band_distance * 5)
        if context.regime == "bull":
            confidence *= 0.95

        if price < lower and rv <= self.rsi_buy and not context.has_position:
            stop = price - (atr_value * 1.2 if atr_value else price * 0.015)
            return StrategySignal(symbol=symbol, side="buy", signal_type="entry", confidence=confidence, stop_loss=stop, reason="oversold_band")
        if (price > upper or rv >= self.rsi_sell) and context.has_position:
            return StrategySignal(symbol=symbol, side="sell", signal_type="exit", confidence=confidence, reason="reversion_exit")
        return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="no_setup")
