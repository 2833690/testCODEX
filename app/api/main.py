from __future__ import annotations

from fastapi import FastAPI

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
from app.core.service import build_bot_service
from app.data.transforms import downsample_candles
from app.exchange.simulated import SimulatedExchangeAdapter
from app.paper.job import PaperTradingJob
from app.strategies.registry import build_strategy
from app.utils.logging import configure_logging

configure_logging()
settings = get_settings()
exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
strategy = build_strategy(settings.strategy.name)
service = build_bot_service(settings=settings, exchange=exchange, strategy=strategy)
paper_job = PaperTradingJob(service=service)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": settings.trading.mode}


@app.get("/config")
def config() -> dict:
    return settings.model_dump()


@app.get("/strategy")
def active_strategy() -> dict[str, str]:
    return {"strategy": strategy.name, "symbol": settings.strategy.symbol, "timeframe": settings.strategy.timeframe}


@app.get("/paper/status")
def paper_status() -> dict:
    p = service.execution.paper_broker.portfolio
    return {
        "cash": p.cash,
        "open_positions": [vars(pos) for pos in p.open_positions],
        "trades": [vars(t) for t in p.trades[-20:]],
        "realized_pnl": p.realized_pnl,
        "max_drawdown": p.max_drawdown,
    }


@app.post("/paper/start")
def start_paper(steps: int = 5) -> dict:
    results = paper_job.start(steps=steps)
    return {"running": paper_job.running, "steps": len(results), "latest": results[-1] if results else None}


@app.post("/paper/stop")
def stop_paper() -> dict[str, bool]:
    paper_job.stop()
    return {"running": paper_job.running}


@app.get("/positions")
def positions() -> list[dict]:
    return [vars(pos) for pos in service.execution.paper_broker.portfolio.open_positions]


@app.get("/trades")
def trades() -> list[dict]:
    return [vars(t) for t in service.execution.paper_broker.portfolio.trades[-50:]]


@app.get("/metrics")
def metrics() -> dict[str, float]:
    p = service.execution.paper_broker.portfolio
    final_equity = p.equity_curve[-1] if p.equity_curve else p.cash
    return compute_metrics(settings.paper_initial_cash, final_equity, p.equity_curve or [settings.paper_initial_cash], p.trades)


@app.get("/diagnostics")
def diagnostics() -> dict:
    p = service.execution.paper_broker.portfolio
    return {
        "risk_state": vars(service.execution.risk_state),
        "equity_points": len(p.equity_curve),
        "trade_count": len(p.trades),
        "trade_quality": trade_quality_diagnostics(p.trades),
        "equity_diagnostics": equity_curve_diagnostics(p.equity_curve, settings.paper_initial_cash),
    }


@app.post("/backtest/run")
def run_backtest() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    engine = BacktestEngine(settings=settings, strategy=strategy)
    paper, curve = engine.run(candles)
    final_equity = curve[-1] if curve else settings.backtest.initial_cash
    return {
        "trades": len(paper.portfolio.trades),
        "final_equity": final_equity,
        "metrics": compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades),
        "trade_quality": trade_quality_diagnostics(paper.portfolio.trades),
        "equity_diagnostics": equity_curve_diagnostics(curve, settings.backtest.initial_cash),
    }


@app.post("/backtest/compare")
def compare_backtests() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    splits = split_walk_forward(candles)
    universe = ["ema_crossover", "mean_reversion", "breakout"]
    metrics_by_strategy: dict[str, dict[str, float]] = {}

    for name in universe:
        strat = build_strategy(name)
        engine = BacktestEngine(settings=settings, strategy=strat)
        dataset = splits["test"] if len(splits["test"]) >= 60 else candles
        paper, curve = engine.run(dataset)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        metrics_by_strategy[name] = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)

    return {"metrics": metrics_by_strategy, "ranking": rank_strategies(metrics_by_strategy)}


@app.post("/research/walk-forward")
def research_walk_forward() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    folds = walk_forward_validation(settings, settings.strategy.name, candles)
    return {"folds": [{"fold": f.fold, "metrics": f.metrics} for f in folds]}


@app.post("/research/sensitivity")
def research_sensitivity() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    if settings.strategy.name == "ema_crossover":
        grid = {"fast_period": [8, 12, 16], "slow_period": [21, 26, 34]}
    elif settings.strategy.name == "mean_reversion":
        grid = {"period": [14, 20, 30], "rsi_buy": [25.0, 30.0, 35.0]}
    else:
        grid = {"lookback": [15, 20, 30], "min_atr_pct": [0.002, 0.003, 0.004]}
    rows = parameter_sensitivity(settings, settings.strategy.name, candles, grid)
    return {"top": rows[:5], "count": len(rows)}


@app.post("/research/stability")
def research_stability() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    datasets = {
        "base_1m": candles,
        "downsampled_5m": downsample_candles(candles, 5),
        "downsampled_15m": downsample_candles(candles, 15),
    }
    return stability_analysis(settings, settings.strategy.name, datasets)
