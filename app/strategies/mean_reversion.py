from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import rsi, sma, stddev


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def __init__(self, period: int = 20, rsi_period: int = 14, rsi_buy: float = 30.0, rsi_sell: float = 70.0) -> None:
        self.period = period
        self.rsi_period = rsi_period
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        closes = [c.close for c in candles]
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))
        mid = sma(closes, self.period)
        sd = stddev(closes, self.period)
        rv = rsi(closes, self.rsi_period)
        if mid is None or sd is None or rv is None:
            return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")
        lower = mid - 2 * sd
        upper = mid + 2 * sd
        price = closes[-1]
        if price < lower and rv <= self.rsi_buy and not context.has_position:
            return StrategySignal(symbol=symbol, side="buy", signal_type="entry", confidence=0.7, stop_loss=price * 0.985, reason="oversold_band")
        if (price > upper or rv >= self.rsi_sell) and context.has_position:
            return StrategySignal(symbol=symbol, side="sell", signal_type="exit", confidence=0.6, reason="reversion_exit")
        return StrategySignal(symbol=symbol, side="buy", signal_type="hold", confidence=0.0, reason="no_setup")
