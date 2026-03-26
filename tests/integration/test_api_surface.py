from app.api.main import (
    available_strategies,
    latest_market_state,
    latest_signal,
    list_backtest_results,
    root,
    run_backtest,
    web_ui,
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


def test_web_interface_routes() -> None:
    redirect_response = root()
    assert redirect_response.headers.get("location") == "/ui"

    html_response = web_ui()
    assert str(html_response.path).endswith("app/api/static/index.html")
