from __future__ import annotations

import json

from app.backtest.engine import BacktestEngine, split_walk_forward
from app.backtest.metrics import compute_metrics, rank_strategies
from app.config.settings import get_settings
from app.exchange.simulated import SimulatedExchangeAdapter
from app.strategies.registry import build_strategy


def run() -> None:
    settings = get_settings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    splits = split_walk_forward(candles)
    strategy_names = ["ema_crossover", "mean_reversion", "breakout"]

    aggregate: dict[str, dict[str, float]] = {}
    for name in strategy_names:
        strat = build_strategy(name)
        settings.strategy.name = name
        engine = BacktestEngine(settings, strat)
        paper, curve = engine.run(splits["test"] if len(splits["test"]) > 35 else candles)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        aggregate[name] = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)

    ranking = rank_strategies(aggregate)
    report = {"metrics": aggregate, "ranking": ranking}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
