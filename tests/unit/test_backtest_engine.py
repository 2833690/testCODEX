from app.backtest.engine import BacktestEngine
from app.config.settings import AppSettings
from app.models.market import Candle
from app.models.trading import StrategyContext, StrategySignal
from app.strategies.base import Strategy


class AlwaysEntryStrategy(Strategy):
    name = "always_entry"

    def generate_signal(self, candles: list[Candle], context: StrategyContext) -> StrategySignal:
        if context.has_position:
            return StrategySignal(symbol="BTC/USDT", side="buy", signal_type="hold", confidence=0.0)
        return StrategySignal(symbol="BTC/USDT", side="buy", signal_type="entry", confidence=0.9, stop_loss=candles[-1].close * 0.98)


def test_backtest_queues_pending_signal_until_latency_matures() -> None:
    settings = AppSettings()
    settings.backtest.latency_bars = 2
    settings.backtest.partial_fill_ratio = 1.0
    engine = BacktestEngine(settings, AlwaysEntryStrategy())

    candles = [
        Candle(timestamp=i * 60_000, open=100 + i * 0.1, high=101 + i * 0.1, low=99 + i * 0.1, close=100 + i * 0.1, volume=500)
        for i in range(120)
    ]

    paper, _ = engine.run(candles)
    assert len(paper.portfolio.open_positions) == 1
