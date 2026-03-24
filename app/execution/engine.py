from __future__ import annotations

from app.config.settings import AppSettings
from app.models.market import MarketSnapshot
from app.models.trading import OrderRequest, StrategySignal
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager, RiskState


class LiveExecutionDisabledError(RuntimeError):
    pass


class ExecutionEngine:
    def __init__(self, settings: AppSettings, paper_broker: PaperBroker, risk_manager: RiskManager) -> None:
        self.settings = settings
        self.paper_broker = paper_broker
        self.risk_manager = risk_manager
        self.risk_state = RiskState()

    def execute_signal(
        self,
        signal: StrategySignal,
        market: MarketSnapshot,
        candles,
    ):
        if signal.signal_type == "hold":
            return None

        portfolio = self.paper_broker.portfolio
        equity = portfolio.update_equity(market.last)

        if signal.signal_type == "entry":
            decision = self.risk_manager.approve(
                signal=signal,
                market=market,
                candles=candles,
                equity=equity,
                open_positions=portfolio.open_positions,
                risk_state=self.risk_state,
            )
            if not decision.approved:
                return {"status": "rejected", "reason": decision.reason}
            req = OrderRequest(symbol=signal.symbol, side="buy", quantity=decision.size)
            return self.paper_broker.place_market_order(req, market_price=market.last, slippage_bps=self.settings.backtest.slippage_bps)

        if signal.signal_type == "exit":
            pos = next((p for p in portfolio.open_positions if p.symbol == signal.symbol), None)
            if not pos:
                return {"status": "ignored", "reason": "no_position"}
            req = OrderRequest(symbol=signal.symbol, side="sell", quantity=pos.quantity)
            result = self.paper_broker.place_market_order(req, market_price=market.last, slippage_bps=self.settings.backtest.slippage_bps)
            if portfolio.trades and portfolio.trades[-1].pnl < 0:
                self.risk_state.consecutive_losses += 1
            elif portfolio.trades:
                self.risk_state.consecutive_losses = 0
            self.risk_state.daily_pnl = portfolio.realized_pnl
            return result
        return None

    def execute_live_order(self) -> None:
        if not self.settings.trading.live_trading_enabled:
            raise LiveExecutionDisabledError("Live execution is disabled by feature flag.")
        raise NotImplementedError("Live execution adapter intentionally stubbed.")
