from __future__ import annotations

from app.models.market import Candle
from app.models.trading import Regime
from app.utils.indicators import ema


def estimate_volatility_pct(candles: list[Candle], lookback: int = 20) -> float:
    if len(candles) < lookback:
        return 0.0
    closes = [c.close for c in candles[-lookback:]]
    if closes[-1] == 0:
        return 0.0
    return (max(closes) - min(closes)) / closes[-1]


def detect_regime(candles: list[Candle], fast: int = 20, slow: int = 50) -> Regime:
    closes = [c.close for c in candles]
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    if fast_ema is None or slow_ema is None:
        return "unknown"
    ratio = (fast_ema - slow_ema) / slow_ema if slow_ema else 0.0
    if ratio > 0.002:
        return "bull"
    if ratio < -0.002:
        return "bear"
    return "sideways"
