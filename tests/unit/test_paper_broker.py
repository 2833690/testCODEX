from app.models.trading import OrderRequest
from app.paper.broker import PaperBroker


def test_partial_fill_buy_and_sell() -> None:
    broker = PaperBroker(initial_cash=10_000, fee_rate=0.001)
    buy = broker.place_market_order(
        OrderRequest(symbol="BTC/USDT", side="buy", quantity=1.0),
        market_price=100,
        partial_fill_ratio=0.5,
    )
    assert buy.status == "partial"
    assert buy.quantity == 0.5

    sell = broker.place_market_order(
        OrderRequest(symbol="BTC/USDT", side="sell", quantity=0.5),
        market_price=101,
        partial_fill_ratio=1.0,
    )
    assert sell.status == "filled"
    assert len(broker.portfolio.trades) == 1


def test_sell_fee_uses_executed_qty_not_requested_qty() -> None:
    broker = PaperBroker(initial_cash=10_000, fee_rate=0.001)
    broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="buy", quantity=1.0), market_price=100, partial_fill_ratio=1.0)
    # request more than available to ensure executed qty is capped at position qty
    result = broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="sell", quantity=2.0), market_price=100, partial_fill_ratio=1.0)
    assert result.quantity == 1.0
    assert result.fee_paid == 0.1


def test_trade_pnl_includes_entry_and_exit_fees() -> None:
    broker = PaperBroker(initial_cash=10_000, fee_rate=0.001)
    broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="buy", quantity=1.0), market_price=100, partial_fill_ratio=1.0)
    broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="sell", quantity=1.0), market_price=101, partial_fill_ratio=1.0)
    trade = broker.portfolio.trades[-1]
    # Gross move is +1.0; net should subtract both entry and exit fees: 0.1 + 0.101
    assert round(trade.pnl, 6) == round(1.0 - 0.1 - 0.101, 6)


def test_additional_buy_updates_weighted_entry_price() -> None:
    broker = PaperBroker(initial_cash=10_000, fee_rate=0.001)
    broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="buy", quantity=1.0), market_price=100, partial_fill_ratio=1.0)
    broker.place_market_order(OrderRequest(symbol="BTC/USDT", side="buy", quantity=1.0), market_price=110, partial_fill_ratio=1.0)
    pos = broker.portfolio.open_positions[0]
    assert len(broker.portfolio.open_positions) == 1
    assert pos.quantity == 2.0
    assert pos.entry_price == 105.0
