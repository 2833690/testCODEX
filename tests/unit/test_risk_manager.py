from app.config.settings import RiskSettings
from app.models.market import Candle, MarketSnapshot
from app.models.trading import StrategySignal
from app.risk.manager import RiskManager, RiskState


def test_position_size_and_gate() -> None:
    manager = RiskManager(RiskSettings())
    market = MarketSnapshot(symbol="BTC/USDT", bid=100, ask=100.01, last=100)
    signal = StrategySignal(symbol="BTC/USDT", side="buy", signal_type="entry", confidence=0.7, stop_loss=99)
    candles = [Candle(timestamp=i, open=100, high=101, low=99, close=100, volume=1) for i in range(40)]
    decision = manager.approve(signal, market, candles, equity=10_000, open_positions=[], risk_state=RiskState())
    assert decision.approved
    assert decision.size > 0


def test_reject_invalid_stop() -> None:
    manager = RiskManager(RiskSettings())
    market = MarketSnapshot(symbol="BTC/USDT", bid=100, ask=101, last=100)
    signal = StrategySignal(symbol="BTC/USDT", side="buy", signal_type="entry", confidence=0.7, stop_loss=100)
    decision = manager.approve(signal, market, [], equity=10_000, open_positions=[], risk_state=RiskState())
    assert not decision.approved
