from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable

from app.config.settings import AppSettings
from app.data.live_feed import CandleFeed
from app.exchange.base import ExchangeAdapter
from app.execution.engine import ExecutionEngine
from app.models.trading import StrategyContext
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager
from app.strategies.base import Strategy
from app.utils.regime import detect_regime, estimate_volatility_pct


@dataclass
class BotService:
    settings: AppSettings
    exchange: ExchangeAdapter
    strategy: Strategy
    execution: ExecutionEngine
    candle_feed: CandleFeed
    latest_market: dict[str, float] | None = None
    latest_signal: dict[str, str | float | None] | None = None
    signal_history: list[dict[str, str | float | None]] = field(default_factory=list)

    def step(self):
        candles = self.candle_feed.latest(limit=200)
        if not candles:
            return {"status": "no_data"}

        market = self.exchange.fetch_ticker(self.settings.strategy.symbol)
        volatility_pct = estimate_volatility_pct(candles)
        context = StrategyContext(
            has_position=any(p.symbol == self.settings.strategy.symbol for p in self.execution.paper_broker.portfolio.open_positions),
            consecutive_losses=self.execution.risk_state.consecutive_losses,
            bars_since_loss=self.execution.risk_state.bars_since_loss,
            regime=detect_regime(candles),
            volatility_pct=volatility_pct,
            metadata={"symbol": self.settings.strategy.symbol},
        )
        signal = self.strategy.generate_signal(candles, context)
        outcome = self.execution.execute_signal(signal=signal, market=market, candles=candles, volatility_pct=volatility_pct)
        equity = self.execution.paper_broker.portfolio.update_equity(market.last)
        self.latest_market = {"bid": market.bid, "ask": market.ask, "last": market.last}
        self.latest_signal = {
            "symbol": signal.symbol,
            "strategy_name": signal.strategy_name,
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
            "regime": context.regime,
        }
        self.signal_history.append(self.latest_signal)
        if len(self.signal_history) > 200:
            self.signal_history = self.signal_history[-200:]
        return {
            "signal": signal,
            "outcome": outcome,
            "equity": equity,
            "cash": self.execution.paper_broker.portfolio.cash,
            "regime": context.regime,
            "volatility_pct": context.volatility_pct,
        }


def build_bot_service(
    settings: AppSettings,
    exchange: ExchangeAdapter,
    strategy: Strategy,
    audit_event: Callable[[str, str, dict], None] | None = None,
) -> BotService:
    paper = PaperBroker(initial_cash=settings.paper_initial_cash, fee_rate=settings.backtest.fee_rate)
    risk = RiskManager(settings.risk)
    execution = ExecutionEngine(settings=settings, paper_broker=paper, risk_manager=risk, audit_event=audit_event)
    feed = CandleFeed(exchange=exchange, symbol=settings.strategy.symbol, timeframe=settings.strategy.timeframe)
    return BotService(settings=settings, exchange=exchange, strategy=strategy, execution=execution, candle_feed=feed)
