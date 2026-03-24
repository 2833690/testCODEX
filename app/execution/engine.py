from __future__ import annotations

from app.config.settings import AppSettings
from app.models.market import Candle, MarketSnapshot
from app.models.trading import OrderRequest, StrategySignal
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager, RiskState
from app.utils.logging import get_logger


class LiveExecutionDisabledError(RuntimeError):
    pass


class ExecutionEngine:
    def __init__(self, settings: AppSettings, paper_broker: PaperBroker, risk_manager: RiskManager) -> None:
        self.settings = settings
        self.paper_broker = paper_broker
        self.risk_manager = risk_manager
        self.risk_state = RiskState()
        self.logger = get_logger("execution_engine")

    def _apply_protective_exits(self, candles: list[Candle]) -> None:
        if not candles:
            return
        last = candles[-1]
        positions = list(self.paper_broker.portfolio.open_positions)
        for pos in positions:
            trigger_price: float | None = None
            trigger_reason = ""
            if pos.stop_loss is not None and last.low <= pos.stop_loss:
                trigger_price = pos.stop_loss
                trigger_reason = "stop_loss"
            elif pos.take_profit is not None and last.high >= pos.take_profit:
                trigger_price = pos.take_profit
                trigger_reason = "take_profit"
            if trigger_price is None:
                continue

            result = self.paper_broker.place_market_order(
                OrderRequest(symbol=pos.symbol, side="sell", quantity=pos.quantity),
                market_price=trigger_price,
                slippage_bps=self.settings.backtest.slippage_bps,
                partial_fill_ratio=1.0,
            )
            self.logger.info("protective_exit", symbol=pos.symbol, reason=trigger_reason, status=result.status, price=trigger_price)
            if result.status == "rejected":
                raise RuntimeError(f"Protective exit failed for {pos.symbol}")

            if self.paper_broker.portfolio.trades and self.paper_broker.portfolio.trades[-1].pnl < 0:
                self.risk_state.consecutive_losses += 1
                self.risk_state.bars_since_loss = 0
            else:
                self.risk_state.consecutive_losses = 0
            self.risk_state.daily_pnl = self.paper_broker.portfolio.realized_pnl

    def execute_signal(
        self,
        signal: StrategySignal,
        market: MarketSnapshot,
        candles: list[Candle],
        volatility_pct: float = 0.0,
        partial_fill_ratio: float | None = None,
    ):
        self.risk_state.bars_since_loss += 1
        self._apply_protective_exits(candles)
        if signal.signal_type == "hold":
            return None

        portfolio = self.paper_broker.portfolio
        equity = portfolio.update_equity(market.last)
        partial = partial_fill_ratio if partial_fill_ratio is not None else self.settings.backtest.partial_fill_ratio

        if signal.signal_type == "entry":
            decision = self.risk_manager.approve(
                signal=signal,
                market=market,
                candles=candles,
                equity=equity,
                peak_equity=max(portfolio.peak_equity, equity),
                open_positions=portfolio.open_positions,
                risk_state=self.risk_state,
                volatility_pct=volatility_pct,
            )
            if not decision.approved:
                self.logger.info("entry_rejected", symbol=signal.symbol, reason=decision.reason)
                return {"status": "rejected", "reason": decision.reason}

            req = OrderRequest(symbol=signal.symbol, side="buy", quantity=decision.size)
            result = self.paper_broker.place_market_order(
                req,
                market_price=market.last,
                slippage_bps=self.settings.backtest.slippage_bps,
                partial_fill_ratio=partial,
            )
            if result.status in {"filled", "partial"}:
                open_pos = next((p for p in reversed(portfolio.open_positions) if p.symbol == signal.symbol), None)
                if open_pos is not None:
                    open_pos.stop_loss = signal.stop_loss
                    open_pos.take_profit = signal.take_profit
            self.logger.info("entry_executed", symbol=signal.symbol, status=result.status, qty=result.quantity)
            return result

        if signal.signal_type == "exit":
            pos = next((p for p in portfolio.open_positions if p.symbol == signal.symbol), None)
            if not pos:
                self.logger.info("exit_ignored", symbol=signal.symbol, reason="no_position")
                return {"status": "ignored", "reason": "no_position"}
            req = OrderRequest(symbol=signal.symbol, side="sell", quantity=pos.quantity)
            result = self.paper_broker.place_market_order(
                req,
                market_price=market.last,
                slippage_bps=self.settings.backtest.slippage_bps,
                partial_fill_ratio=partial,
            )
            if portfolio.trades and portfolio.trades[-1].pnl < 0:
                self.risk_state.consecutive_losses += 1
                self.risk_state.bars_since_loss = 0
            elif portfolio.trades:
                self.risk_state.consecutive_losses = 0
            self.risk_state.daily_pnl = portfolio.realized_pnl
            self.logger.info("exit_executed", symbol=signal.symbol, status=result.status, qty=result.quantity)
            return result

        return None

    def execute_live_order(self) -> None:
        if not self.settings.trading.live_trading_enabled:
            raise LiveExecutionDisabledError("Live execution is disabled by feature flag.")
        raise NotImplementedError("Live execution adapter intentionally stubbed.")
