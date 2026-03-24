from app.utils.indicators import atr, ema, rsi, sma


def test_sma_and_ema() -> None:
    prices = [1, 2, 3, 4, 5, 6]
    assert sma(prices, 3) == 5
    assert ema(prices, 3) is not None


def test_rsi_range() -> None:
    prices = [1, 2, 3, 2, 3, 4, 3, 4, 5, 4, 5, 6, 5, 6, 7, 8]
    value = rsi(prices, 14)
    assert value is not None
    assert 0 <= value <= 100


def test_atr_positive() -> None:
    highs = [10, 11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13, 14]
    closes = [9.5, 10.5, 11.5, 12.5, 13.5, 14.5]
    value = atr(highs, lows, closes, period=3)
    assert value is not None
    assert value > 0
