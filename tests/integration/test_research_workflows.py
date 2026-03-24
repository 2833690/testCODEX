from app.backtest.analysis import stability_analysis, walk_forward_validation
from app.config.settings import AppSettings
from app.data.transforms import downsample_candles
from app.exchange.simulated import SimulatedExchangeAdapter


def test_walk_forward_produces_folds() -> None:
    settings = AppSettings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    folds = walk_forward_validation(settings, settings.strategy.name, candles, train_size=100, test_size=40, step_size=20)
    assert len(folds) > 0
    assert "sortino_like" in folds[0].metrics


def test_stability_analysis_produces_score() -> None:
    settings = AppSettings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    datasets = {
        "1m": candles,
        "5m": downsample_candles(candles, 5),
    }
    result = stability_analysis(settings, settings.strategy.name, datasets)
    assert "stability_score" in result
    assert "per_dataset" in result
