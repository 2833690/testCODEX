from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.backtest.analysis import (
    equity_curve_diagnostics,
    parameter_sensitivity,
    stability_analysis,
    trade_quality_diagnostics,
    walk_forward_validation,
)
from app.backtest.diagnostics import (
    metrics_by_symbol_timeframe,
    regime_performance_breakdown,
    streak_analysis,
    trade_distribution_analysis,
)
from app.backtest.engine import BacktestEngine, split_walk_forward
from app.backtest.metrics import compute_metrics, rank_strategies
from app.config.settings import get_settings
from app.core.service import build_bot_service
from app.data.transforms import downsample_candles
from app.exchange.simulated import SimulatedExchangeAdapter
from app.paper.job import PaperTradingJob
from app.storage import SqliteRepository
from app.strategies.registry import STRATEGY_BUILDERS, build_strategy
from app.utils.logging import configure_logging

configure_logging()
settings = get_settings()
repository = SqliteRepository(settings.storage.sqlite_path)


def _audit_event(event_type: str, status: str, details: dict) -> None:
    repository.save_event(event_type=event_type, status=status, details=details)


exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
strategy = build_strategy(settings.strategy.name)
service = build_bot_service(settings=settings, exchange=exchange, strategy=strategy, audit_event=_audit_event)
paper_job = PaperTradingJob(service=service)
backtest_runs: list[dict] = []

app = FastAPI(title=settings.app_name)
UI_DIR = Path(__file__).with_name("static")
app.mount("/ui/assets", StaticFiles(directory=UI_DIR), name="ui-assets")


def envelope(data: dict | list, message: str = "ok") -> dict:
    return {"status": "ok", "message": message, "data": data}


def _serialize_step_result(step_result: dict) -> dict:
    signal = step_result.get("signal")
    outcome = step_result.get("outcome")
    serialized_signal = vars(signal) if signal is not None and not isinstance(signal, dict) else signal
    serialized_outcome = vars(outcome) if outcome is not None and not isinstance(outcome, dict) else outcome
    return {
        "signal": serialized_signal,
        "outcome": serialized_outcome,
        "equity": step_result.get("equity"),
        "cash": step_result.get("cash"),
        "regime": step_result.get("regime"),
        "volatility_pct": step_result.get("volatility_pct"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return envelope({"mode": settings.trading.mode, "live_enabled": settings.trading.live_trading_enabled, "kill_switch_enabled": settings.trading.kill_switch_enabled})


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.get("/ui")
def web_ui() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/config")
def config() -> dict:
    cfg = settings.model_dump()
    cfg["api_key"] = "***" if settings.api_key else None
    cfg["api_secret"] = "***" if settings.api_secret else None
    return envelope(cfg)


@app.get("/strategy")
def active_strategy() -> dict[str, str]:
    return envelope({"strategy": strategy.name, "symbol": settings.strategy.symbol, "timeframe": settings.strategy.timeframe})


@app.get("/strategies")
def available_strategies() -> dict[str, list[str]]:
    return envelope({"strategies": sorted(STRATEGY_BUILDERS.keys())})


@app.get("/market/latest")
def latest_market_state() -> dict:
    if service.latest_market is None:
        service.step()
    return envelope({
        "symbol": settings.strategy.symbol,
        "timeframe": settings.strategy.timeframe,
        "market": service.latest_market,
    })


@app.get("/signals/latest")
def latest_signal() -> dict:
    if service.latest_signal is None:
        service.step()
    return envelope({"active_strategy": strategy.name, "signal": service.latest_signal})


@app.get("/signals/history")
def signal_history(limit: int = 50) -> dict:
    bounded_limit = max(1, min(limit, 200))
    return envelope({"count": min(bounded_limit, len(service.signal_history)), "signals": service.signal_history[-bounded_limit:]})


@app.get("/signals/persisted")
def persisted_signals(limit: int = 100) -> dict:
    return envelope({"signals": repository.list_signals(limit=max(1, min(limit, 500)))})


@app.get("/paper/status")
def paper_status() -> dict:
    p = service.execution.paper_broker.portfolio
    return envelope({
        "cash": p.cash,
        "open_positions": [vars(pos) for pos in p.open_positions],
        "trades": [vars(t) for t in p.trades[-20:]],
        "realized_pnl": p.realized_pnl,
        "max_drawdown": p.max_drawdown,
    })


@app.post("/paper/start")
def start_paper(steps: int = 5) -> dict:
    initial_trade_count = len(service.execution.paper_broker.portfolio.trades)
    results = paper_job.start(steps=steps)
    serialized_results = [_serialize_step_result(r) for r in results]
    for r in results:
        signal = r.get("signal")
        if signal is not None:
            signal_payload = {
                "strategy_name": signal.strategy_name,
                "symbol": signal.symbol,
                "side": signal.side,
                "signal_type": signal.signal_type,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "key_features": signal.key_features,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "stop_loss_basis": signal.stop_loss_basis,
                "invalidation_condition": signal.invalidation_condition,
                "explanation": signal.explanation,
            }
            repository.save_signal(signal_payload, timeframe=settings.strategy.timeframe)
    for trade in service.execution.paper_broker.portfolio.trades[initial_trade_count:]:
        repository.save_trade(vars(trade))
    repository.save_run(
        run_type="paper",
        strategy=strategy.name,
        symbol=settings.strategy.symbol,
        timeframe=settings.strategy.timeframe,
        payload={"steps": len(serialized_results), "latest": serialized_results[-1] if serialized_results else None},
    )
    return envelope({"running": paper_job.running, "steps": len(serialized_results), "latest": serialized_results[-1] if serialized_results else None}, message="paper run completed")


@app.post("/paper/stop")
def stop_paper() -> dict[str, bool]:
    paper_job.stop()
    repository.save_event("paper_stop", "ok", {"running": paper_job.running})
    return envelope({"running": paper_job.running})


@app.get("/positions")
def positions() -> list[dict]:
    return envelope([vars(pos) for pos in service.execution.paper_broker.portfolio.open_positions])


@app.get("/trades")
def trades() -> list[dict]:
    return envelope([vars(t) for t in service.execution.paper_broker.portfolio.trades[-50:]])


@app.get("/metrics")
def metrics() -> dict[str, float]:
    p = service.execution.paper_broker.portfolio
    final_equity = p.equity_curve[-1] if p.equity_curve else p.cash
    metrics_payload = compute_metrics(settings.paper_initial_cash, final_equity, p.equity_curve or [settings.paper_initial_cash], p.trades)
    return envelope(metrics_payload)


@app.get("/diagnostics")
def diagnostics() -> dict:
    p = service.execution.paper_broker.portfolio
    return envelope({
        "risk_state": vars(service.execution.risk_state),
        "equity_points": len(p.equity_curve),
        "trade_count": len(p.trades),
        "trade_quality": trade_quality_diagnostics(p.trades),
        "equity_diagnostics": equity_curve_diagnostics(p.equity_curve, settings.paper_initial_cash),
        "trade_distribution": trade_distribution_analysis(p.trades),
        "streaks": streak_analysis(p.trades),
        "regime_breakdown": regime_performance_breakdown(service.signal_history, p.trades),
        "metrics_by_symbol_timeframe": metrics_by_symbol_timeframe(p.trades, settings.strategy.timeframe),
    })


@app.post("/backtest/run")
def run_backtest() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    engine = BacktestEngine(settings=settings, strategy=strategy)
    paper, curve = engine.run(candles)
    final_equity = curve[-1] if curve else settings.backtest.initial_cash
    result = {
        "trades": len(paper.portfolio.trades),
        "final_equity": final_equity,
        "metrics": compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades),
        "trade_quality": trade_quality_diagnostics(paper.portfolio.trades),
        "equity_diagnostics": equity_curve_diagnostics(curve, settings.backtest.initial_cash),
    }
    backtest_runs.append(result)
    if len(backtest_runs) > 100:
        del backtest_runs[:-100]
    repository.save_run("backtest", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, result)
    return envelope(result, message="backtest completed")


@app.get("/backtest/results")
def list_backtest_results() -> dict:
    persisted = repository.list_runs(run_type="backtest", limit=50)
    return envelope({"in_memory_count": len(backtest_runs), "recent": backtest_runs[-20:], "persisted": persisted})


@app.get("/paper/runs")
def list_paper_runs(limit: int = 50) -> dict:
    return envelope({"runs": repository.list_runs(run_type="paper", limit=max(1, min(limit, 500)))})


@app.get("/events/audit")
def list_audit_events(limit: int = 100) -> dict:
    return envelope({"events": repository.list_events(limit=max(1, min(limit, 500)))})


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

    report = {"metrics": metrics_by_strategy, "ranking": rank_strategies(metrics_by_strategy)}
    repository.save_run("comparison", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, report)
    return envelope(report)


@app.post("/research/walk-forward")
def research_walk_forward() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    folds = walk_forward_validation(settings, settings.strategy.name, candles)
    payload = {"folds": [{"fold": f.fold, "chosen_params": f.chosen_params, "metrics": f.metrics} for f in folds]}
    repository.save_run("walk_forward", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, payload)
    return envelope(payload)


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
    payload = {"top": rows[:5], "count": len(rows)}
    repository.save_run("sensitivity", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, payload)
    return envelope(payload)


@app.post("/research/stability")
def research_stability() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    datasets = {
        "base_1m": candles,
        "downsampled_5m": downsample_candles(candles, 5),
        "downsampled_15m": downsample_candles(candles, 15),
    }
    payload = stability_analysis(settings, settings.strategy.name, datasets)
    repository.save_run("stability", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, payload)
    return envelope(payload)


@app.post("/research/split")
def research_split() -> dict:
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=500)
    splits = split_walk_forward(candles)
    metrics: dict[str, dict[str, float]] = {}
    for split_name, dataset in splits.items():
        if not dataset:
            continue
        engine = BacktestEngine(settings=settings, strategy=strategy)
        paper, curve = engine.run(dataset)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        metrics[split_name] = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)
    payload = {"sizes": {k: len(v) for k, v in splits.items()}, "metrics": metrics}
    repository.save_run("split", strategy.name, settings.strategy.symbol, settings.strategy.timeframe, payload)
    return envelope(payload)


@app.get("/reports/backtests/export")
def export_backtests(format: str = "json") -> Response:
    runs = repository.list_runs(run_type="backtest", limit=200)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["id", "strategy", "symbol", "timeframe", "created_at", "trades", "final_equity", "net_return", "max_drawdown"])
        writer.writeheader()
        for r in runs:
            payload = r.get("payload", {})
            metrics_payload = payload.get("metrics", {})
            writer.writerow(
                {
                    "id": r["id"],
                    "strategy": r["strategy"],
                    "symbol": r["symbol"],
                    "timeframe": r["timeframe"],
                    "created_at": r["created_at"],
                    "trades": payload.get("trades", 0),
                    "final_equity": payload.get("final_equity", 0.0),
                    "net_return": metrics_payload.get("net_return", 0.0),
                    "max_drawdown": metrics_payload.get("max_drawdown", 0.0),
                }
            )
        return Response(content=buf.getvalue(), media_type="text/csv")
    return JSONResponse(content=envelope({"runs": runs}))
