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

    def place_market_order(
        self,
        request: OrderRequest,
        market_price: float,
        slippage_bps: float = 0.0,
        partial_fill_ratio: float = 1.0,
        fill_timestamp_ms: int | None = None,
    ) -> OrderResult:
        order_id = f"paper-{next(self._order_seq)}"
        slip_mult = 1 + (slippage_bps / 10_000 if request.side == "buy" else -slippage_bps / 10_000)
        fill_price = market_price * slip_mult
        requested_fill_qty = request.quantity * max(0.1, min(partial_fill_ratio, 1.0))

        if request.side == "buy":
            notional = fill_price * requested_fill_qty
            fee = notional * self.fee_rate
            cost = notional + fee
            if cost > self.portfolio.cash:
                return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=0.0, average_price=fill_price, fee_paid=0.0, status="rejected")
            self.portfolio.cash -= cost
            existing = next((p for p in self.portfolio.open_positions if p.symbol == request.symbol and p.side == "buy"), None)
            if existing is None:
                self.portfolio.open_positions.append(
                    Position(
                        symbol=request.symbol,
                        side="buy",
                        quantity=requested_fill_qty,
                        entry_price=fill_price,
                        stop_loss=None,
                        take_profit=None,
                        entry_fee_paid=fee,
                    )
                )
            else:
                combined_qty = existing.quantity + requested_fill_qty
                if combined_qty > 0:
                    existing.entry_price = ((existing.entry_price * existing.quantity) + (fill_price * requested_fill_qty)) / combined_qty
                existing.quantity = combined_qty
                existing.entry_fee_paid += fee
            status = "filled" if requested_fill_qty >= request.quantity else "partial"
            return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=requested_fill_qty, average_price=fill_price, fee_paid=fee, status=status)

        pos = next((p for p in self.portfolio.open_positions if p.symbol == request.symbol and p.side == "buy"), None)
        if pos is None:
            return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=0.0, average_price=fill_price, fee_paid=0.0, status="rejected")

        qty = min(requested_fill_qty, pos.quantity)
        notional = qty * fill_price
        fee = notional * self.fee_rate
        proceeds = notional - fee
        entry_fee_alloc = pos.entry_fee_paid * (qty / pos.quantity) if pos.quantity > 0 else 0.0
        pnl = (fill_price - pos.entry_price) * qty - fee - entry_fee_alloc
        self.portfolio.cash += proceeds
        pos.quantity -= qty
        pos.entry_fee_paid = max(0.0, pos.entry_fee_paid - entry_fee_alloc)
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
                timestamp=fill_timestamp_ms if fill_timestamp_ms is not None else int(time() * 1000),
            )
        )
        if pos.quantity <= 0:
            self.portfolio.open_positions.remove(pos)
        status = "filled" if qty >= request.quantity else "partial"
        return OrderResult(order_id=order_id, symbol=request.symbol, side=request.side, quantity=qty, average_price=fill_price, fee_paid=fee, status=status)
