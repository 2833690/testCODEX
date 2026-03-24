from app.models.market import Candle
from app.utils.regime import detect_regime, estimate_volatility_pct


def test_detect_regime_bull() -> None:
    candles = [Candle(timestamp=i, open=100 + i, high=101 + i, low=99 + i, close=100 + i, volume=1) for i in range(80)]
    assert detect_regime(candles) == "bull"


def test_estimate_volatility_pct_non_negative() -> None:
    candles = [Candle(timestamp=i, open=100, high=101, low=99, close=100 + (i % 2), volume=1) for i in range(30)]
    vol = estimate_volatility_pct(candles)
    assert vol >= 0
