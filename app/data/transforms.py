from __future__ import annotations

from app.models.market import Candle


def downsample_candles(candles: list[Candle], factor: int) -> list[Candle]:
    if factor <= 1:
        return candles
    output: list[Candle] = []
    for i in range(0, len(candles), factor):
        chunk = candles[i : i + factor]
        if len(chunk) < factor:
            break
        output.append(
            Candle(
                timestamp=chunk[-1].timestamp,
                open=chunk[0].open,
                high=max(c.high for c in chunk),
                low=min(c.low for c in chunk),
                close=chunk[-1].close,
                volume=sum(c.volume for c in chunk),
            )
        )
    return output
