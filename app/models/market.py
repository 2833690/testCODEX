from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    bid: float
    ask: float
    last: float

    @property
    def spread_bps(self) -> float:
        mid = (self.bid + self.ask) / 2
        if mid == 0:
            return 0.0
        return (self.ask - self.bid) / mid * 10_000
