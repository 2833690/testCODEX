from __future__ import annotations

from statistics import fmean


def sma(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    return fmean(values[-period:])


def ema(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    k = 2 / (period + 1)
    current = fmean(values[:period])
    for price in values[period:]:
        current = price * k + current * (1 - k)
    return current


def stddev(values: list[float], period: int) -> float | None:
    if period <= 1 or len(values) < period:
        return None
    window = values[-period:]
    mean = fmean(window)
    var = sum((v - mean) ** 2 for v in window) / period
    return var ** 0.5


def rsi(values: list[float], period: int = 14) -> float | None:
    if period <= 0 or len(values) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(-period, 0):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = fmean(gains)
    avg_loss = fmean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    if len(highs) != len(lows) or len(lows) != len(closes) or len(closes) < period + 1:
        return None
    true_ranges: list[float] = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)
    if len(true_ranges) < period:
        return None
    return fmean(true_ranges[-period:])
