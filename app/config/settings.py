from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RiskSettings(BaseModel):
    max_risk_per_trade: float = Field(default=0.01, ge=0.0, le=0.05)
    max_daily_loss_pct: float = Field(default=0.03, ge=0.0, le=0.2)
    max_drawdown_pct: float = Field(default=0.2, ge=0.01, le=0.9)
    max_concurrent_positions: int = Field(default=3, ge=1, le=20)
    min_notional: float = Field(default=10.0, ge=1.0)
    max_notional: float = Field(default=10_000.0, ge=10.0)
    min_confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    min_stop_distance_pct: float = Field(default=0.0025, ge=0.0, le=0.2)
    target_volatility_pct: float = Field(default=0.02, ge=0.0, le=0.2)
    max_spread_bps: float = Field(default=20.0, ge=0.0)
    max_volatility_pct: float = Field(default=0.08, ge=0.0)
    cooldown_bars_after_losses: int = Field(default=3, ge=0, le=100)
    consecutive_losses_limit: int = Field(default=2, ge=1, le=20)


    @model_validator(mode="after")
    def validate_notional_bounds(self) -> "RiskSettings":
        if self.min_notional >= self.max_notional:
            raise ValueError("min_notional must be less than max_notional")
        return self


class BacktestSettings(BaseModel):
    fee_rate: float = Field(default=0.001, ge=0.0, le=0.01)
    slippage_bps: float = Field(default=5.0, ge=0.0, le=100.0)
    spread_bps: float = Field(default=2.0, ge=0.0, le=200.0)
    latency_bars: int = Field(default=1, ge=1, le=5)
    partial_fill_ratio: float = Field(default=1.0, ge=0.1, le=1.0)
    initial_cash: float = Field(default=10_000.0, ge=100.0)


class TradingSettings(BaseModel):
    mode: Literal["paper", "live"] = "paper"
    live_trading_enabled: bool = False
    kill_switch_enabled: bool = True
    circuit_breaker_failures: int = Field(default=3, ge=1, le=20)

    @model_validator(mode="after")
    def validate_live_mode(self) -> "TradingSettings":
        if self.mode == "live" and not self.live_trading_enabled:
            raise ValueError("mode=live requires live_trading_enabled=true")
        return self


class StrategySettings(BaseModel):
    name: Literal["ema_crossover", "mean_reversion", "breakout", "volatility_breakout", "regime_filter"] = "ema_crossover"
    timeframe: str = "1m"
    symbol: str = "BTC/USDT"


class StorageSettings(BaseModel):
    storage_dir: str = "storage"
    datasets_dir: str = "storage/datasets"
    reports_dir: str = "storage/reports"
    persist_signals: bool = True
    persist_trades: bool = True
    persist_runs: bool = True


class ExecutionSettings(BaseModel):
    order_timeout_seconds: float = Field(default=8.0, ge=1.0, le=120.0)
    retry_attempts: int = Field(default=2, ge=0, le=10)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    app_name: str = "reliable-crypto-bot"
    environment: Literal["dev", "test", "prod"] = "dev"
    exchange: Literal["binance", "bybit"] = "binance"

    api_key: str | None = None
    api_secret: str | None = None

    poll_interval_seconds: float = Field(default=5.0, ge=1.0, le=120.0)
    paper_initial_cash: float = Field(default=10_000.0, ge=100.0)

    trading: TradingSettings = TradingSettings()
    strategy: StrategySettings = StrategySettings()
    risk: RiskSettings = RiskSettings()
    backtest: BacktestSettings = BacktestSettings()
    storage: StorageSettings = StorageSettings()
    execution: ExecutionSettings = ExecutionSettings()

    @model_validator(mode="after")
    def validate_secret_requirements(self) -> "AppSettings":
        if self.trading.mode == "live":
            if not self.api_key or not self.api_secret:
                raise ValueError("api_key and api_secret are required in live mode")
        return self


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
