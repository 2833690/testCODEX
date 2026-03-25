from __future__ import annotations

from collections import defaultdict
from statistics import fmean
from typing import Any

from app.models.trading import TradeRecord


def trade_distribution_analysis(trades: list[TradeRecord]) -> dict[str, float]:
    if not trades:
        return {"pnl_p10": 0.0, "pnl_p50": 0.0, "pnl_p90": 0.0, "avg_holding_bars_proxy": 0.0}
    pnls = sorted(t.pnl for t in trades)

    def pct(p: float) -> float:
        idx = int((len(pnls) - 1) * p)
        return pnls[idx]

    return {
        "pnl_p10": pct(0.1),
        "pnl_p50": pct(0.5),
        "pnl_p90": pct(0.9),
        "avg_holding_bars_proxy": 1.0,
    }


def streak_analysis(trades: list[TradeRecord]) -> dict[str, float]:
    longest_win = 0
    longest_loss = 0
    current_win = 0
    current_loss = 0
    for t in trades:
        if t.pnl > 0:
            current_win += 1
            current_loss = 0
        elif t.pnl < 0:
            current_loss += 1
            current_win = 0
        else:
            current_win = 0
            current_loss = 0
        longest_win = max(longest_win, current_win)
        longest_loss = max(longest_loss, current_loss)
    return {"longest_win_streak": float(longest_win), "longest_loss_streak": float(longest_loss)}


def metrics_by_symbol_timeframe(trades: list[TradeRecord], timeframe: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        key = f"{t.symbol}|{timeframe}"
        grouped[key].append(t.pnl)
    out: dict[str, dict[str, float]] = {}
    for key, pnls in grouped.items():
        wins = [p for p in pnls if p > 0]
        out[key] = {
            "trade_count": float(len(pnls)),
            "win_rate": float(len(wins) / len(pnls)) if pnls else 0.0,
            "avg_pnl": float(fmean(pnls)) if pnls else 0.0,
            "total_pnl": float(sum(pnls)),
        }
    return out


def regime_performance_breakdown(signals: list[dict[str, Any]], trades: list[TradeRecord]) -> dict[str, dict[str, float]]:
    if not signals or not trades:
        return {}
    # Approximation: map recent non-hold entry/exit signals to executed trades in sequence.
    actionable = [s for s in signals if s.get("signal_type") in {"entry", "exit"}]
    by_regime: dict[str, list[float]] = defaultdict(list)
    for idx, t in enumerate(trades):
        signal_idx = min(idx, len(actionable) - 1)
        regime = str(actionable[signal_idx].get("regime", "unknown"))
        by_regime[regime].append(t.pnl)
    return {
        regime: {
            "trades": float(len(pnls)),
            "avg_pnl": float(fmean(pnls)) if pnls else 0.0,
            "total_pnl": float(sum(pnls)),
            "win_rate": float(sum(1 for p in pnls if p > 0) / len(pnls)) if pnls else 0.0,
        }
        for regime, pnls in by_regime.items()
    }
