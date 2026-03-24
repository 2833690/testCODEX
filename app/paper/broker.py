from __future__ import annotations

import itertools
from time import time

from app.models.trading import OrderRequest, OrderResult, Position, TradeRecord
from app.portfolio.state import PortfolioState


class PaperBroker:
    def __init__(self, initial_cash: float, fee_rate: float = 0.001) -> None:
        self.portfolio = PortfolioState(cash=initial_cash)
        self.fee_rate = fee_rate
        self._order_seq = itertools.count(1)

    def place_market_order(self, request: OrderRequest, market_price: float, slippage_bps: float = 0.0) -> OrderResult:
        order_id = f"paper-{next(self._order_seq)}"
        slip_mult = 1 + (slippage_bps / 10_000 if request.side == "buy" else -slippage_bps / 10_000)
        fill_price = market_price * slip_mult
        notional = fill_price * request.quantity
        fee = notional * self.fee_rate

        if request.side == "buy":
            cost = notional + fee
            if cost > self.portfolio.cash:
                return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=0.0, average_price=fill_price, fee_paid=0.0, status="rejected")
            self.portfolio.cash -= cost
            self.portfolio.open_positions.append(
                Position(symbol=request.symbol, side="buy", quantity=request.quantity, entry_price=fill_price, stop_loss=None, take_profit=None)
            )
        else:
            pos = next((p for p in self.portfolio.open_positions if p.symbol == request.symbol and p.side == "buy"), None)
            if pos is None:
                return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=0.0, average_price=fill_price, fee_paid=0.0, status="rejected")
            qty = min(request.quantity, pos.quantity)
            proceeds = qty * fill_price - fee
            pnl = (fill_price - pos.entry_price) * qty - fee
            self.portfolio.cash += proceeds
            pos.quantity -= qty
            self.portfolio.trades.append(
                TradeRecord(
                    order_id=order_id,
                    symbol=request.symbol,
                    side=request.side,
                    quantity=qty,
                    entry_price=pos.entry_price,
                    exit_price=fill_price,
                    pnl=pnl,
                    fee=fee,
                    timestamp=int(time() * 1000),
                )
            )
            if pos.quantity <= 0:
                self.portfolio.open_positions.remove(pos)
        return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=request.quantity, average_price=fill_price, fee_paid=fee, status="filled")
