from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from statistics import fmean
from typing import Any

from app.backtest.engine import BacktestEngine
from app.backtest.metrics import compute_metrics, rank_strategies
from app.config.settings import AppSettings
from app.models.market import Candle
from app.models.trading import TradeRecord
from app.strategies.registry import build_strategy


@dataclass
class FoldResult:
    fold: int
    train_start: int
    train_end: int
    val_start: int
    val_end: int
    test_start: int
    test_end: int
    chosen_params: dict[str, Any]
    metrics: dict[str, float]


def _equity_drawdown_durations(equity_curve: list[float]) -> tuple[int, float]:
    if not equity_curve:
        return 0, 0.0
    peak = equity_curve[0]
    duration = 0
    max_duration = 0
    drawdowns: list[float] = []
    for e in equity_curve:
        if e >= peak:
            peak = e
            duration = 0
        else:
            duration += 1
            drawdowns.append((peak - e) / peak if peak else 0.0)
            max_duration = max(max_duration, duration)
    ulcer = (fmean([d * d for d in drawdowns]) ** 0.5) if drawdowns else 0.0
    return max_duration, ulcer


def _default_grid(strategy_name: str) -> dict[str, list[Any]]:
    if strategy_name == "ema_crossover":
        return {"fast_period": [8, 12, 16], "slow_period": [21, 26, 34]}
    if strategy_name == "mean_reversion":
        return {"period": [14, 20, 30], "rsi_buy": [25.0, 30.0, 35.0]}
    return {"lookback": [15, 20, 30], "min_atr_pct": [0.002, 0.003, 0.004]}


def trade_quality_diagnostics(trades: list[TradeRecord]) -> dict[str, float]:
    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    avg_win = fmean(wins) if wins else 0.0
    avg_loss = abs(fmean(losses)) if losses else 0.0
    payoff_ratio = (avg_win / avg_loss) if avg_loss else 0.0
    return {
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": payoff_ratio,
        "win_count": float(len(wins)),
        "loss_count": float(len(losses)),
    }


def equity_curve_diagnostics(equity_curve: list[float], initial_cash: float) -> dict[str, float]:
    max_dd_duration, ulcer_index = _equity_drawdown_durations(equity_curve)
    final_equity = equity_curve[-1] if equity_curve else initial_cash
    net_return = (final_equity - initial_cash) / initial_cash if initial_cash else 0.0
    recovery_factor = (net_return / ulcer_index) if ulcer_index > 0 else 0.0
    return {
        "max_drawdown_duration_bars": float(max_dd_duration),
        "ulcer_index": ulcer_index,
        "recovery_factor": recovery_factor,
    }


def walk_forward_validation(
    settings: AppSettings,
    strategy_name: str,
    candles: list[Candle],
    train_size: int = 120,
    test_size: int = 40,
    step_size: int = 20,
) -> list[FoldResult]:
    # Adapt fold sizing for smaller deterministic datasets used in local tests/demo.
    n = len(candles)
    if n < train_size + test_size:
        if n < 12:
            return []
        train_size = max(8, int(n * 0.6))
        test_size = max(4, min(int(n * 0.25), n - train_size))
        step_size = max(1, min(step_size, test_size))

    folds: list[FoldResult] = []
    start = 0
    fold_id = 1
    grid = _default_grid(strategy_name)

    while start + train_size + test_size <= len(candles):
        train_slice = candles[start : start + train_size]
        test_slice = candles[start + train_size : start + train_size + test_size]
        min_train = max(8, int(train_size * 0.6))
        min_test = max(4, int(test_size * 0.6))
        if len(train_slice) < min_train or len(test_slice) < min_test:
            break

        train_cut = int(len(train_slice) * 0.7)
        inner_train = train_slice[:train_cut]
        inner_val = train_slice[train_cut:]

        # tune on inner-train/inner-validation
        candidates = parameter_sensitivity(settings, strategy_name, inner_train, grid)
        top = candidates[:5] if len(candidates) >= 5 else candidates
        best_params: dict[str, Any] = {}
        best_score = float("-inf")
        for c in top:
            params = c["params"]
            strategy = build_strategy(strategy_name, **params)
            engine = BacktestEngine(settings, strategy)
            paper, curve = engine.run(inner_val)
            final_equity = curve[-1] if curve else settings.backtest.initial_cash
            metrics = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)
            score = metrics.get("sortino_like", 0.0) - metrics.get("max_drawdown", 0.0)
            if score > best_score:
                best_score = score
                best_params = params

        # evaluate best params on test only
        strategy = build_strategy(strategy_name, **best_params)
        engine = BacktestEngine(settings, strategy)
        paper, curve = engine.run(test_slice)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        metrics = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)
        metrics.update(equity_curve_diagnostics(curve, settings.backtest.initial_cash))

        folds.append(
            FoldResult(
                fold=fold_id,
                train_start=start,
                train_end=start + train_cut - 1,
                val_start=start + train_cut,
                val_end=start + train_size - 1,
                test_start=start + train_size,
                test_end=start + train_size + test_size - 1,
                chosen_params=best_params,
                metrics=metrics,
            )
        )
        start += step_size
        fold_id += 1
    return folds


def parameter_sensitivity(
    settings: AppSettings,
    strategy_name: str,
    candles: list[Candle],
    grid: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    keys = list(grid.keys())
    rows: list[dict[str, Any]] = []
    for values in product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values, strict=True))
        strategy = build_strategy(strategy_name, **params)
        engine = BacktestEngine(settings, strategy)
        paper, curve = engine.run(candles)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        metrics = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)
        rows.append({"params": params, "metrics": metrics})
    rows.sort(key=lambda x: x["metrics"].get("sortino_like", 0.0), reverse=True)
    return rows


def stability_analysis(
    settings: AppSettings,
    strategy_name: str,
    datasets: dict[str, list[Candle]],
) -> dict[str, Any]:
    per_dataset: dict[str, dict[str, float]] = {}
    for label, candles in datasets.items():
        strategy = build_strategy(strategy_name)
        engine = BacktestEngine(settings, strategy)
        paper, curve = engine.run(candles)
        final_equity = curve[-1] if curve else settings.backtest.initial_cash
        metrics = compute_metrics(settings.backtest.initial_cash, final_equity, curve or [settings.backtest.initial_cash], paper.portfolio.trades)
        metrics.update(equity_curve_diagnostics(curve, settings.backtest.initial_cash))
        per_dataset[label] = metrics

    ranking = rank_strategies({f"{strategy_name}:{k}": v for k, v in per_dataset.items()})
    sortinos = [m.get("sortino_like", 0.0) for m in per_dataset.values()]
    returns = [m.get("net_return", 0.0) for m in per_dataset.values()]
    stability_score = (fmean(sortinos) - (max(sortinos) - min(sortinos) if sortinos else 0.0)) + (fmean(returns) if returns else 0.0)
    consistency = float(sum(1 for r in returns if r > 0) / len(returns)) if returns else 0.0
    return {"per_dataset": per_dataset, "ranking": ranking, "stability_score": stability_score, "consistency": consistency}
