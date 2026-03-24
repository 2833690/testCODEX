from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings
from app.execution.engine import ExecutionEngine
from app.models.market import Candle, MarketSnapshot
from app.models.trading import StrategyContext
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager
from app.strategies.base import Strategy


@dataclass
class BacktestResult:
    trades: int
    final_equity: float
    metrics: dict[str, float]


class BacktestEngine:
    def __init__(self, settings: AppSettings, strategy: Strategy) -> None:
        self.settings = settings
        self.strategy = strategy

    def run(self, candles: list[Candle]) -> tuple[PaperBroker, list[float]]:
        paper = PaperBroker(self.settings.backtest.initial_cash, fee_rate=self.settings.backtest.fee_rate)
        risk = RiskManager(self.settings.risk)
        execution = ExecutionEngine(self.settings, paper, risk)
        equity_curve: list[float] = []
        for i in range(30, len(candles)):
            window = candles[: i + 1]
            last = window[-1]
            snapshot = MarketSnapshot(symbol=self.settings.strategy.symbol, bid=last.close * 0.9999, ask=last.close * 1.0001, last=last.close)
            context = StrategyContext(
                has_position=any(p.symbol == self.settings.strategy.symbol for p in paper.portfolio.open_positions),
                consecutive_losses=execution.risk_state.consecutive_losses,
                metadata={"symbol": self.settings.strategy.symbol},
            )
            signal = self.strategy.generate_signal(window, context)
            execution.execute_signal(signal, snapshot, window)
            equity_curve.append(paper.portfolio.update_equity(last.close))
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
