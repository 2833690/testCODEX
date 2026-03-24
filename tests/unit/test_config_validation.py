import pytest

from app.config.settings import AppSettings, BacktestSettings, TradingSettings


def test_default_mode_is_paper() -> None:
    settings = AppSettings()
    assert settings.trading.mode == "paper"
    assert settings.trading.live_trading_enabled is False


def test_live_mode_requires_flag() -> None:
    with pytest.raises(ValueError):
        TradingSettings(mode="live", live_trading_enabled=False)


def test_backtest_latency_minimum() -> None:
    with pytest.raises(ValueError):
        BacktestSettings(latency_bars=0)


def test_risk_drawdown_validation() -> None:
    with pytest.raises(ValueError):
        AppSettings(risk={"max_drawdown_pct": 0.0})


def test_notional_bounds_validation() -> None:
    with pytest.raises(ValueError):
        AppSettings(risk={"min_notional": 100, "max_notional": 50})
