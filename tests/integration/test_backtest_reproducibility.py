from app.backtest.engine import BacktestEngine
from app.config.settings import AppSettings
from app.exchange.simulated import SimulatedExchangeAdapter
from app.strategies.registry import build_strategy


def test_backtest_reproducibility() -> None:
    settings = AppSettings()
    settings.strategy.name = "ema_crossover"
    strategy = build_strategy(settings.strategy.name)
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)

    engine = BacktestEngine(settings, strategy)
    paper1, curve1 = engine.run(candles)
    paper2, curve2 = engine.run(candles)

    assert len(paper1.portfolio.trades) == len(paper2.portfolio.trades)
    assert curve1 == curve2
