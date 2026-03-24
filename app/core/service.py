from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings
from app.data.live_feed import CandleFeed
from app.exchange.base import ExchangeAdapter
from app.execution.engine import ExecutionEngine
from app.models.trading import StrategyContext
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager
from app.strategies.base import Strategy


@dataclass
class BotService:
    settings: AppSettings
    exchange: ExchangeAdapter
    strategy: Strategy
    execution: ExecutionEngine
    candle_feed: CandleFeed

    def step(self):
        candles = self.candle_feed.latest(limit=200)
        if not candles:
            return {"status": "no_data"}
        market = self.exchange.fetch_ticker(self.settings.strategy.symbol)
        context = StrategyContext(
            has_position=any(p.symbol == self.settings.strategy.symbol for p in self.execution.paper_broker.portfolio.open_positions),
            consecutive_losses=self.execution.risk_state.consecutive_losses,
            metadata={"symbol": self.settings.strategy.symbol},
        )
        signal = self.strategy.generate_signal(candles, context)
        outcome = self.execution.execute_signal(signal=signal, market=market, candles=candles)
        equity = self.execution.paper_broker.portfolio.update_equity(market.last)
        return {
            "signal": signal,
            "outcome": outcome,
            "equity": equity,
            "cash": self.execution.paper_broker.portfolio.cash,
        }


def build_bot_service(settings: AppSettings, exchange: ExchangeAdapter, strategy: Strategy) -> BotService:
    paper = PaperBroker(initial_cash=settings.paper_initial_cash, fee_rate=settings.backtest.fee_rate)
    risk = RiskManager(settings.risk)
    execution = ExecutionEngine(settings=settings, paper_broker=paper, risk_manager=risk)
    feed = CandleFeed(exchange=exchange, symbol=settings.strategy.symbol, timeframe=settings.strategy.timeframe)
    return BotService(settings=settings, exchange=exchange, strategy=strategy, execution=execution, candle_feed=feed)
