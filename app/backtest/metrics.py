from __future__ import annotations

from statistics import fmean

from app.models.trading import TradeRecord


def compute_metrics(initial_cash: float, final_equity: float, equity_curve: list[float], trades: list[TradeRecord]) -> dict[str, float]:
    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = len(wins) / len(pnls) if pnls else 0.0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    expectancy = fmean(pnls) if pnls else 0.0
    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] != 0:
            returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])
    avg_ret = fmean(returns) if returns else 0.0
    vol = (fmean([(r - avg_ret) ** 2 for r in returns]) ** 0.5) if returns else 0.0
    sharpe_like = (avg_ret / vol) * (len(returns) ** 0.5) if vol > 0 else 0.0
    max_dd = 0.0
    peak = equity_curve[0] if equity_curve else initial_cash
    for e in equity_curve:
        peak = max(peak, e)
        if peak > 0:
            max_dd = max(max_dd, (peak - e) / peak)
    net_return = (final_equity - initial_cash) / initial_cash

    return {
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "sharpe_like": sharpe_like,
        "expectancy": expectancy,
        "net_return": net_return,
    }


def rank_strategies(results: dict[str, dict[str, float]]) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for name, metrics in results.items():
        score = (
            metrics["sharpe_like"] * 0.5
            + metrics["net_return"] * 0.3
            - metrics["max_drawdown"] * 0.2
        )
        scored.append((name, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)
