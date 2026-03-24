from unittest.mock import MagicMock, patch

from app.exchange.ccxt_adapter import CcxtExchangeAdapter
from app.models.trading import OrderRequest


@patch("app.exchange.ccxt_adapter.ccxt.binance")
def test_ccxt_adapter_market_data(mock_exchange_cls) -> None:
    mock_client = MagicMock()
    mock_client.fetch_ohlcv.return_value = [[1, 1, 2, 0.5, 1.5, 100]]
    mock_client.fetch_ticker.return_value = {"bid": 10, "ask": 11, "last": 10.5}
    mock_client.fetch_balance.return_value = {"total": {"USDT": 1000}}
    mock_exchange_cls.return_value = mock_client

    adapter = CcxtExchangeAdapter("binance")
    candles = adapter.fetch_ohlcv("BTC/USDT", "1m", limit=1)
    ticker = adapter.fetch_ticker("BTC/USDT")
    balance = adapter.fetch_balance()

    assert candles[0].close == 1.5
    assert ticker.last == 10.5
    assert balance["USDT"] == 1000


@patch("app.exchange.ccxt_adapter.ccxt.binance")
def test_ccxt_adapter_create_order(mock_exchange_cls) -> None:
    mock_client = MagicMock()
    mock_client.create_order.return_value = {
        "id": "abc",
        "filled": 1,
        "average": 100,
        "fee": {"cost": 0.1},
        "status": "closed",
    }
    mock_exchange_cls.return_value = mock_client
    adapter = CcxtExchangeAdapter("binance")
    result = adapter.create_order(OrderRequest(symbol="BTC/USDT", side="buy", quantity=1))
    assert result.order_id == "abc"
    assert result.status == "filled"
