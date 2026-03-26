from app.strategies.registry import STRATEGY_BUILDERS


def test_required_strategies_present() -> None:
    assert "breakout" in STRATEGY_BUILDERS
    assert "mean_reversion" in STRATEGY_BUILDERS
    assert "volatility_breakout" in STRATEGY_BUILDERS
    assert "regime_filter" in STRATEGY_BUILDERS
