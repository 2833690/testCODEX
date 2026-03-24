from __future__ import annotations

import json

from app.backtest.analysis import (
    equity_curve_diagnostics,
    parameter_sensitivity,
    stability_analysis,
    trade_quality_diagnostics,
    walk_forward_validation,
)
from app.backtest.engine import BacktestEngine, split_walk_forward
from app.backtest.metrics import compute_metrics, rank_strategies
from app.config.settings import get_settings
from app.data.transforms import downsample_candles
from app.exchange.simulated import SimulatedExchangeAdapter
from app.strategies.registry import build_strategy


def run() -> None:
    settings = get_settings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    splits = split_walk_forward(candles)
    strategy_names = ["ema_crossover", "mean_reversion", "breakout"]

    aggregate: dict[str, dict[str, float]] = {}
    strategy_diagnostics: dict[str, dict] = {}
    for name in strategy_names:
        strat = build_strategy(name)
        engine = BacktestEngine(settings, strat)
        dataset = splits["test"] if len(splits["test"]) >= 60 else candles
        paper, curve = engine.run(dataset)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        aggregate[name] = compute_metrics(
            settings.backtest.initial_cash,
            final_equity,
            curve or [settings.backtest.initial_cash],
            paper.portfolio.trades,
        )
        strategy_diagnostics[name] = {
            "trade_quality": trade_quality_diagnostics(paper.portfolio.trades),
            "equity_diagnostics": equity_curve_diagnostics(curve, settings.backtest.initial_cash),
        }

    ranking = rank_strategies(aggregate)
    walk_forward = walk_forward_validation(settings, settings.strategy.name, candles)
    sensitivity = parameter_sensitivity(
        settings,
        settings.strategy.name,
        candles,
        {"fast_period": [8, 12, 16], "slow_period": [21, 26, 34]} if settings.strategy.name == "ema_crossover" else {"lookback": [15, 20, 30]},
    )
    stability = stability_analysis(
        settings,
        settings.strategy.name,
        {
            "base_1m": candles,
            "downsampled_5m": downsample_candles(candles, 5),
            "downsampled_15m": downsample_candles(candles, 15),
        },
    )

    report = {
        "assumptions": {
            "fee_rate": settings.backtest.fee_rate,
            "slippage_bps": settings.backtest.slippage_bps,
            "spread_bps": settings.backtest.spread_bps,
            "latency_bars": settings.backtest.latency_bars,
        },
        "metrics": aggregate,
        "ranking": ranking,
        "diagnostics": strategy_diagnostics,
        "walk_forward": [{"fold": f.fold, "metrics": f.metrics} for f in walk_forward],
        "sensitivity_top": sensitivity[:5],
        "stability": stability,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
