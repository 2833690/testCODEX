from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Side = Literal["buy", "sell"]
SignalType = Literal["entry", "exit", "hold"]
Regime = Literal["bull", "bear", "sideways", "unknown"]


@dataclass(frozen=True)
class StrategySignal:
    symbol: str
    side: Side
    signal_type: SignalType
    confidence: float
    stop_loss: float | None = None
    take_profit: float | None = None
    reason: str = ""


@dataclass
class Position:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    entry_fee_paid: float = 0.0


@dataclass
class OrderRequest:
    symbol: str
    side: Side
    quantity: float
    order_type: Literal["market"] = "market"


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: Side
    quantity: float
    average_price: float
    fee_paid: float
    status: Literal["filled", "partial", "rejected"]


@dataclass
class TradeRecord:
    order_id: str
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    fee: float
    timestamp: int


@dataclass
class RiskDecision:
    approved: bool
    reason: str = ""
    size: float = 0.0


@dataclass
class StrategyContext:
    has_position: bool
    consecutive_losses: int = 0
    bars_since_loss: int = 9999
    regime: Regime = "unknown"
    volatility_pct: float = 0.0
    metadata: dict[str, float | str] = field(default_factory=dict)
