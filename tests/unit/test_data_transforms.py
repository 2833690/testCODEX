from app.data.transforms import downsample_candles
from app.models.market import Candle


def test_downsample_candles_groups_ohlcv() -> None:
    candles = [
        Candle(timestamp=i, open=100 + i, high=101 + i, low=99 + i, close=100 + i, volume=1.0)
        for i in range(10)
    ]
    out = downsample_candles(candles, factor=5)
    assert len(out) == 2
    assert out[0].open == candles[0].open
    assert out[0].close == candles[4].close
    assert out[0].volume == 5.0
