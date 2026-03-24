from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings
from app.execution.engine import ExecutionEngine
from app.models.market import Candle, MarketSnapshot
from app.models.trading import StrategyContext, StrategySignal
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager
from app.strategies.base import Strategy
from app.utils.regime import detect_regime, estimate_volatility_pct


@dataclass
class BacktestResult:
    trades: int
    final_equity: float
    metrics: dict[str, float]


class BacktestEngine:
    def __init__(self, settings: AppSettings, strategy: Strategy) -> None:
        self.settings = settings
        self.strategy = strategy

    def _snapshot_from_candle(self, symbol: str, candle: Candle) -> MarketSnapshot:
        half_spread = (self.settings.backtest.spread_bps / 10_000) / 2
        bid = candle.open * (1 - half_spread)
        ask = candle.open * (1 + half_spread)
        return MarketSnapshot(symbol=symbol, bid=bid, ask=ask, last=candle.open)

    def run(self, candles: list[Candle]) -> tuple[PaperBroker, list[float]]:
        paper = PaperBroker(self.settings.backtest.initial_cash, fee_rate=self.settings.backtest.fee_rate)
        risk = RiskManager(self.settings.risk)
        execution = ExecutionEngine(self.settings, paper, risk)
        equity_curve: list[float] = []
        pending_signals: list[tuple[int, StrategySignal]] = []

        warmup = 50
        latency = self.settings.backtest.latency_bars

        for i in range(warmup, len(candles)):
            history = candles[: i + 1]
            current = candles[i]
            volatility_pct = estimate_volatility_pct(history)

            matured_signals = [item for item in pending_signals if item[0] <= i]
            pending_signals = [item for item in pending_signals if item[0] > i]
            for _, matured_signal in matured_signals:
                fill_candle = current
                pre_fill_history = candles[:i]
                snapshot = self._snapshot_from_candle(self.settings.strategy.symbol, fill_candle)
                reference_volume = pre_fill_history[-1].volume if pre_fill_history else fill_candle.volume
                dynamic_partial = min(1.0, max(0.2, reference_volume / 300.0))
                execution.execute_signal(
                    signal=matured_signal,
                    market=snapshot,
                    candles=pre_fill_history,
                    volatility_pct=estimate_volatility_pct(pre_fill_history),
                    partial_fill_ratio=min(dynamic_partial, self.settings.backtest.partial_fill_ratio),
                )

            context = StrategyContext(
                has_position=any(p.symbol == self.settings.strategy.symbol for p in paper.portfolio.open_positions),
                consecutive_losses=execution.risk_state.consecutive_losses,
                bars_since_loss=execution.risk_state.bars_since_loss,
                regime=detect_regime(history),
                volatility_pct=volatility_pct,
                metadata={"symbol": self.settings.strategy.symbol},
            )
            next_signal = self.strategy.generate_signal(history, context)
            if next_signal.signal_type in {"entry", "exit"}:
                pending_signals.append((i + latency, next_signal))
            equity_curve.append(paper.portfolio.update_equity(current.close))
        return paper, equity_curve


def split_walk_forward(candles: list[Candle], train_ratio: float = 0.6, val_ratio: float = 0.2) -> dict[str, list[Candle]]:
    n = len(candles)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    return {
        "train": candles[:train_end],
        "validation": candles[train_end:val_end],
        "test": candles[val_end:],
    }
