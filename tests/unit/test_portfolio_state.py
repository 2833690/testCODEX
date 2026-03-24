from app.models.trading import Position
from app.portfolio.state import PortfolioState


def test_equity_includes_mark_to_market_value_for_open_positions() -> None:
    portfolio = PortfolioState(cash=900.0)
    portfolio.open_positions.append(
        Position(symbol="BTC/USDT", side="buy", quantity=1.0, entry_price=100.0, stop_loss=None, take_profit=None)
    )
    equity = portfolio.update_equity(mark_price=100.0)
    assert equity == 1000.0


def test_equity_changes_with_mark_price_for_open_position() -> None:
    portfolio = PortfolioState(cash=900.0)
    portfolio.open_positions.append(
        Position(symbol="BTC/USDT", side="buy", quantity=1.0, entry_price=100.0, stop_loss=None, take_profit=None)
    )
    equity = portfolio.update_equity(mark_price=105.0)
    assert equity == 1005.0
