from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import RiskSettings
from app.models.market import Candle, MarketSnapshot
from app.models.trading import Position, RiskDecision, StrategySignal


@dataclass
class RiskState:
    daily_pnl: float = 0.0
    consecutive_losses: int = 0
    bars_since_loss: int = 9999
    day_start_equity: float = 0.0
    current_day: int | None = None
    day_start_realized_pnl: float = 0.0


class RiskManager:
    def __init__(self, settings: RiskSettings) -> None:
        self.settings = settings

    def position_size(self, equity: float, entry: float, stop_loss: float, volatility_pct: float = 0.0) -> float:
        if stop_loss <= 0 or entry <= stop_loss:
            return 0.0
        if entry <= 0:
            return 0.0
        risk_budget = equity * self.settings.max_risk_per_trade
        stop_distance = entry - stop_loss
        size = risk_budget / stop_distance

        if volatility_pct > 0:
            vol_scale = min(1.0, self.settings.target_volatility_pct / volatility_pct)
            size *= max(0.2, vol_scale)

        notional = size * entry
        if notional < self.settings.min_notional:
            return 0.0
        if notional > self.settings.max_notional:
            size = self.settings.max_notional / entry
        return max(size, 0.0)

    def approve(
        self,
        signal: StrategySignal,
        market: MarketSnapshot,
        candles: list[Candle],
        equity: float,
        peak_equity: float,
        open_positions: list[Position],
        risk_state: RiskState,
        volatility_pct: float = 0.0,
        current_day: int | None = None,
    ) -> RiskDecision:
        if signal.signal_type != "entry":
            return RiskDecision(approved=True, size=0.0)
        if current_day is not None and risk_state.current_day != current_day:
            risk_state.current_day = current_day
            risk_state.day_start_equity = equity
            risk_state.day_start_realized_pnl = risk_state.daily_pnl
        if risk_state.day_start_equity <= 0:
            risk_state.day_start_equity = equity

        if signal.confidence < self.settings.min_confidence:
            return RiskDecision(approved=False, reason="low_confidence")
        if signal.stop_loss is None or signal.stop_loss >= market.last:
            return RiskDecision(approved=False, reason="invalid_stop_loss")

        stop_distance_pct = (market.last - signal.stop_loss) / market.last if market.last else 0.0
        if stop_distance_pct < self.settings.min_stop_distance_pct:
            return RiskDecision(approved=False, reason="stop_too_tight")

        if peak_equity > 0:
            drawdown = max(0.0, (peak_equity - equity) / peak_equity)
            if drawdown > self.settings.max_drawdown_pct:
                return RiskDecision(approved=False, reason="drawdown_guardrail")

        if len(open_positions) >= self.settings.max_concurrent_positions:
            return RiskDecision(approved=False, reason="max_concurrent_positions")

        daily_loss_limit = risk_state.day_start_equity * self.settings.max_daily_loss_pct
        session_pnl = risk_state.daily_pnl - risk_state.day_start_realized_pnl
        if session_pnl < -daily_loss_limit:
            return RiskDecision(approved=False, reason="daily_loss_limit")

        if (
            risk_state.consecutive_losses >= self.settings.consecutive_losses_limit
            and risk_state.bars_since_loss < self.settings.cooldown_bars_after_losses
        ):
            return RiskDecision(approved=False, reason="cooldown_after_losses")
        if market.spread_bps > self.settings.max_spread_bps:
            return RiskDecision(approved=False, reason="spread_too_wide")

        if len(candles) >= 20:
            closes = [c.close for c in candles[-20:]]
            observed_volatility = (max(closes) - min(closes)) / closes[-1]
            if observed_volatility > self.settings.max_volatility_pct:
                return RiskDecision(approved=False, reason="volatility_too_high")
            if volatility_pct <= 0:
                volatility_pct = observed_volatility

        size = self.position_size(equity=equity, entry=market.last, stop_loss=signal.stop_loss, volatility_pct=volatility_pct)
        if size <= 0.0:
            return RiskDecision(approved=False, reason="invalid_position_size")
        return RiskDecision(approved=True, size=size)
