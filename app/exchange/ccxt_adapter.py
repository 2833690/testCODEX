from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import ccxt

from app.exchange.base import ExchangeAdapter
from app.models.market import Candle, MarketSnapshot
from app.models.trading import OrderRequest, OrderResult


class RetryableExchangeError(RuntimeError):
    pass


class CcxtExchangeAdapter(ExchangeAdapter):
    def __init__(
        self,
        exchange_name: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        exchange_cls = getattr(ccxt, exchange_name)
        self.client = exchange_cls(
            {
                "apiKey": api_key or "",
                "secret": api_secret or "",
                "enableRateLimit": True,
            }
        )
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def _run_with_retry(self, fn: Callable[[], Any]) -> Any:
        attempt = 0
        while True:
            attempt += 1
            try:
                return fn()
            except (ccxt.NetworkError, ccxt.RequestTimeout) as exc:
                if attempt >= self.retries:
                    raise RetryableExchangeError(str(exc)) from exc
                time.sleep(self.retry_delay_seconds)

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        raw = self._run_with_retry(lambda: self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit))
        return [
            Candle(timestamp=r[0], open=float(r[1]), high=float(r[2]), low=float(r[3]), close=float(r[4]), volume=float(r[5]))
            for r in raw
        ]

    def fetch_ticker(self, symbol: str) -> MarketSnapshot:
        t = self._run_with_retry(lambda: self.client.fetch_ticker(symbol))
        bid = float(t.get("bid") or t.get("last") or 0.0)
        ask = float(t.get("ask") or t.get("last") or bid)
        last = float(t.get("last") or bid)
        return MarketSnapshot(symbol=symbol, bid=bid, ask=ask, last=last)

    def fetch_balance(self) -> dict[str, float]:
        bal = self._run_with_retry(self.client.fetch_balance)
        total = bal.get("total", {})
        return {k: float(v) for k, v in total.items() if isinstance(v, (int, float))}

    def create_order(self, request: OrderRequest) -> OrderResult:
        o = self._run_with_retry(
            lambda: self.client.create_order(
                symbol=request.symbol,
                type=request.order_type,
                side=request.side,
                amount=request.quantity,
            )
        )
        filled = float(o.get("filled") or 0.0)
        cost = float(o.get("cost") or 0.0)
        avg = float(o.get("average") or (cost / filled if filled else 0.0))
        fee = o.get("fee", {}) or {}
        return OrderResult(
            order_id=str(o.get("id")),
            symbol=request.symbol,
            side=request.side,
            quantity=filled,
            average_price=avg,
            fee_paid=float(fee.get("cost") or 0.0),
            status="filled" if o.get("status") == "closed" else "partial",
        )

    def fetch_order(self, order_id: str, symbol: str) -> OrderResult:
        o = self._run_with_retry(lambda: self.client.fetch_order(id=order_id, symbol=symbol))
        filled = float(o.get("filled") or 0.0)
        avg = float(o.get("average") or 0.0)
        fee = o.get("fee", {}) or {}
        status = "filled" if o.get("status") == "closed" else "partial"
        if o.get("status") in {"canceled", "rejected"}:
            status = "rejected"
        return OrderResult(
            order_id=order_id,
            symbol=symbol,
            side=str(o.get("side")),
            quantity=filled,
            average_price=avg,
            fee_paid=float(fee.get("cost") or 0.0),
            status=status,
        )
