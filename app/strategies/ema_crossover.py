from __future__ import annotations

from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy
from app.utils.indicators import atr, ema


class EmaCrossoverStrategy(Strategy):
    name = "ema_crossover"

    def __init__(self, fast_period: int = 12, slow_period: int = 26, atr_period: int = 14) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        fast = ema(closes, self.fast_period)
        slow = ema(closes, self.slow_period)
        atr_value = atr(highs, lows, closes, self.atr_period)
        symbol = str(context.metadata.get("symbol", "BTC/USDT"))
        if fast is None or slow is None:
            return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="insufficient_data")

        trend_gap = abs(fast - slow) / closes[-1]
        confidence = min(0.9, 0.55 + trend_gap * 10)
        if context.regime == "bear":
            confidence *= 0.85

        if fast > slow and not context.has_position:
            stop = closes[-1] - (atr_value * 1.8 if atr_value else closes[-1] * 0.01)
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="buy",
                signal_type="entry",
                confidence=confidence,
                stop_loss=stop,
                reason="fast_above_slow",
                key_features={"fast_ema": round(fast, 4), "slow_ema": round(slow, 4), "trend_gap_pct": round(trend_gap * 100, 4)},
                stop_loss_basis="1.8x ATR below entry",
                invalidation_condition="fast EMA crosses back below slow EMA",
                explanation="EMA trend is positive and no position is open; enter long with ATR-based stop.",
            )
        if fast < slow and context.has_position:
            return StrategySignal(
                symbol=symbol,
                strategy_name=self.name,
                side="sell",
                signal_type="exit",
                confidence=confidence,
                reason="fast_below_slow",
                key_features={"fast_ema": round(fast, 4), "slow_ema": round(slow, 4)},
                stop_loss_basis="N/A (exit signal)",
                invalidation_condition="trend re-accelerates up with fast EMA above slow EMA",
                explanation="Momentum weakened: fast EMA moved below slow EMA while in position.",
            )
        return StrategySignal(symbol=symbol, strategy_name=self.name, side="buy", signal_type="hold", confidence=0.0, reason="no_change")
