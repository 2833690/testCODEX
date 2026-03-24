from __future__ import annotations

VALID_TIMEFRAMES = {"1m", "5m", "15m", "1h", "4h", "1d"}


def validate_symbol(symbol: str) -> None:
    if "/" not in symbol:
        raise ValueError(f"Invalid symbol format: {symbol}")


def validate_timeframe(timeframe: str) -> None:
    if timeframe not in VALID_TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
