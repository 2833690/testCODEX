from __future__ import annotations

from dataclasses import dataclass, field

from app.models.trading import Position, TradeRecord


@dataclass
class PortfolioState:
    cash: float
    open_positions: list[Position] = field(default_factory=list)
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    peak_equity: float = 0.0
    max_drawdown: float = 0.0

    @property
    def realized_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    def update_equity(self, mark_price: float) -> float:
        unrealized = 0.0
        for pos in self.open_positions:
            if pos.side == "buy":
                unrealized += (mark_price - pos.entry_price) * pos.quantity
            else:
                unrealized += (pos.entry_price - mark_price) * pos.quantity
        equity = self.cash + unrealized
        self.equity_curve.append(equity)
        if equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, dd)
        return equity
