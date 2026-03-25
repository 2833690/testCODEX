from app.models.market import Candle
from app.models.trading import StrategyContext
from app.strategies.breakout import BreakoutStrategy
from app.strategies.ema_crossover import EmaCrossoverStrategy
from app.strategies.mean_reversion import MeanReversionStrategy


def mk_candles() -> list[Candle]:
    out = []
    base = 100.0
    for i in range(40):
        c = base + i * 0.2
        out.append(Candle(timestamp=i, open=c - 0.1, high=c + 0.2, low=c - 0.3, close=c, volume=1.0))
    return out


def test_ema_crossover_signal_shape() -> None:
    strategy = EmaCrossoverStrategy()
    signal = strategy.generate_signal(mk_candles(), StrategyContext(has_position=False, metadata={"symbol": "BTC/USDT"}))
    assert signal.signal_type in {"entry", "exit", "hold"}
    assert signal.strategy_name == "ema_crossover"
    if signal.signal_type in {"entry", "exit"}:
        assert signal.explanation
        assert signal.invalidation_condition


def test_mean_reversion_signal_shape() -> None:
    strategy = MeanReversionStrategy()
    signal = strategy.generate_signal(mk_candles(), StrategyContext(has_position=False, metadata={"symbol": "BTC/USDT"}))
    assert signal.signal_type in {"entry", "exit", "hold"}
    assert signal.strategy_name == "mean_reversion"
    if signal.signal_type in {"entry", "exit"}:
        assert signal.explanation
        assert signal.stop_loss_basis


def test_breakout_signal_shape() -> None:
    strategy = BreakoutStrategy()
    signal = strategy.generate_signal(mk_candles(), StrategyContext(has_position=False, metadata={"symbol": "BTC/USDT"}))
    assert signal.signal_type in {"entry", "exit", "hold"}
    assert signal.strategy_name == "breakout"
    if signal.signal_type in {"entry", "exit"}:
        assert signal.explanation
        assert signal.key_features is not None
