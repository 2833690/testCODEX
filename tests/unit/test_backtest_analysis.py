from app.backtest.analysis import (
    equity_curve_diagnostics,
    parameter_sensitivity,
    trade_quality_diagnostics,
)
from app.config.settings import AppSettings
from app.exchange.simulated import SimulatedExchangeAdapter


def test_trade_quality_diagnostics_basic() -> None:
    class T:
        def __init__(self, pnl: float) -> None:
            self.pnl = pnl

    d = trade_quality_diagnostics([T(10.0), T(-5.0), T(2.0)])
    assert d["avg_win"] > 0
    assert d["avg_loss"] > 0


def test_equity_curve_diagnostics_basic() -> None:
    d = equity_curve_diagnostics([100, 95, 97, 90, 110], 100)
    assert d["ulcer_index"] >= 0
    assert d["max_drawdown_duration_bars"] >= 0


def test_parameter_sensitivity_returns_ranked_rows() -> None:
    settings = AppSettings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    candles = exchange.fetch_ohlcv(settings.strategy.symbol, settings.strategy.timeframe, limit=200)
    rows = parameter_sensitivity(settings, "ema_crossover", candles, {"fast_period": [8, 12], "slow_period": [21, 26]})
    assert len(rows) == 4
    assert rows[0]["metrics"].get("sortino_like") >= rows[-1]["metrics"].get("sortino_like")
