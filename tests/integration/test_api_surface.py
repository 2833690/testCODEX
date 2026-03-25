from app.api.main import (
    available_strategies,
    latest_market_state,
    latest_signal,
    list_backtest_results,
    run_backtest,
)


def test_strategy_and_signal_endpoints() -> None:
    strategies = available_strategies()
    assert "data" in strategies
    assert "strategies" in strategies["data"]
    assert "ema_crossover" in strategies["data"]["strategies"]

    latest_market = latest_market_state()
    assert latest_market["data"]["market"] is not None

    signal = latest_signal()
    assert signal["data"]["signal"] is not None


def test_backtest_results_tracking() -> None:
    run_backtest()
    results = list_backtest_results()
    assert results["data"]["in_memory_count"] >= 1
    assert len(results["data"]["recent"]) >= 1
