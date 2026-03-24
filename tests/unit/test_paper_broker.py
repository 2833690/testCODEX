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
