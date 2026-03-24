from app.backtest.engine import BacktestEngine, split_walk_forward
from app.backtest.metrics import rank_strategies
from app.config.settings import AppSettings
from app.exchange.simulated import SimulatedExchangeAdapter
from app.strategies.registry import build_strategy


def test_backtest_reproducibility() -> None:
    settings = AppSettings()
    strategy = build_strategy("ema_crossover")
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)

    engine = BacktestEngine(settings, strategy)
    paper1, curve1 = engine.run(candles)
    paper2, curve2 = engine.run(candles)

    assert len(paper1.portfolio.trades) == len(paper2.portfolio.trades)
    assert curve1 == curve2


def test_walk_forward_splits_are_ordered_and_non_overlapping() -> None:
    settings = AppSettings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    splits = split_walk_forward(candles)
    assert splits["train"]
    assert splits["validation"]
    assert splits["test"]
    assert splits["train"][-1].timestamp < splits["validation"][0].timestamp
    assert splits["validation"][-1].timestamp < splits["test"][0].timestamp


def test_strategy_ranking_orders_scores_desc() -> None:
    ranking = rank_strategies(
        {
            "a": {"sortino_like": 2.0, "sharpe_like": 1.5, "calmar_like": 1.0, "net_return": 0.2, "max_drawdown": 0.1},
            "b": {"sortino_like": 0.8, "sharpe_like": 0.7, "calmar_like": 0.4, "net_return": 0.1, "max_drawdown": 0.2},
        }
    )
    assert ranking[0][0] == "a"
