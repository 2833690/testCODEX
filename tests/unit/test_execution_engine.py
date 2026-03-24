from app.config.settings import AppSettings
from app.execution.engine import ExecutionEngine
from app.models.market import Candle, MarketSnapshot
from app.models.trading import StrategySignal
from app.paper.broker import PaperBroker
from app.risk.manager import RiskManager


def test_entry_sets_stop_loss_and_take_profit() -> None:
    settings = AppSettings()
    broker = PaperBroker(initial_cash=10_000, fee_rate=settings.backtest.fee_rate)
    engine = ExecutionEngine(settings, broker, RiskManager(settings.risk))
    signal = StrategySignal(
        symbol=settings.strategy.symbol,
        side="buy",
        signal_type="entry",
        confidence=0.9,
        stop_loss=99,
        take_profit=102,
    )
    candle = Candle(timestamp=1, open=100, high=101, low=99.5, close=100, volume=100)
    market = MarketSnapshot(symbol=settings.strategy.symbol, bid=99.9, ask=100.1, last=100)
    engine.execute_signal(signal, market, [candle], volatility_pct=0.01)
    pos = broker.portfolio.open_positions[0]
    assert pos.stop_loss == 99
    assert pos.take_profit == 102


def test_protective_stop_exits_position() -> None:
    settings = AppSettings()
    broker = PaperBroker(initial_cash=10_000, fee_rate=settings.backtest.fee_rate)
    engine = ExecutionEngine(settings, broker, RiskManager(settings.risk))

    entry = StrategySignal(symbol=settings.strategy.symbol, side="buy", signal_type="entry", confidence=0.9, stop_loss=99)
    market = MarketSnapshot(symbol=settings.strategy.symbol, bid=99.9, ask=100.1, last=100)
    entry_candle = Candle(timestamp=1, open=100, high=100.5, low=99.8, close=100, volume=150)
    engine.execute_signal(entry, market, [entry_candle], volatility_pct=0.01)

    risk_candle = Candle(timestamp=2, open=100, high=100.2, low=98.5, close=99, volume=200)
    hold = StrategySignal(symbol=settings.strategy.symbol, side="buy", signal_type="hold", confidence=0.0)
    engine.execute_signal(hold, market, [entry_candle, risk_candle], volatility_pct=0.01)

    assert len(broker.portfolio.open_positions) == 0
    assert len(broker.portfolio.trades) >= 1


def test_entry_uses_ask_and_exit_uses_bid() -> None:
    settings = AppSettings()
    broker = PaperBroker(initial_cash=10_000, fee_rate=settings.backtest.fee_rate)
    engine = ExecutionEngine(settings, broker, RiskManager(settings.risk))
    market = MarketSnapshot(symbol=settings.strategy.symbol, bid=99.0, ask=101.0, last=100.0)
    candle = Candle(timestamp=1, open=100, high=102, low=99, close=100, volume=100)

    entry = StrategySignal(symbol=settings.strategy.symbol, side="buy", signal_type="entry", confidence=0.9, stop_loss=95)
    engine.execute_signal(entry, market, [candle], volatility_pct=0.01)
    pos = broker.portfolio.open_positions[0]
    assert pos.entry_price >= market.ask

    exit_signal = StrategySignal(symbol=settings.strategy.symbol, side="sell", signal_type="exit", confidence=0.9)
    engine.execute_signal(exit_signal, market, [candle], volatility_pct=0.01)
    trade = broker.portfolio.trades[-1]
    assert trade.exit_price <= market.bid
