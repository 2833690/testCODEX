# Reliable Crypto Bot (Paper First)

Production-minded algorithmic trading framework for Binance (default) with adapter-ready architecture for Bybit.

## Safety-first defaults

- **Default mode: paper trading**.
- **Live trading is feature-flagged and disabled by default**.
- No secrets in code. Use environment variables from `.env`.
- Backtests account for **fees, spread, slippage, latency, and partial fills**.
- Strategy metrics are evaluated after costs and ranked by risk-adjusted robustness.
- All entry orders pass through mandatory risk checks.

## Architecture

```text
app/
  api/            FastAPI endpoints
  config/         Pydantic settings and validation
  core/           Bot composition and orchestration
  exchange/       CCXT + simulation adapters
  data/           OHLCV loading, validation, feed abstraction/transforms
  strategies/     Pure strategy modules (no exchange calls)
  risk/           Mandatory pre-trade risk checks and sizing
  execution/      Signal -> order translation
  portfolio/      Portfolio/account state
  backtest/       Backtest engine, metrics, research analysis
  paper/          Paper broker and paper job orchestration
  models/         Shared typed domain objects
  utils/          Logging, indicators, and regime utilities
tests/
  unit/
  integration/
scripts/
  run_paper.py
  run_backtest.py
```

## Senior-quant audit outcomes addressed

### Hidden failure modes mitigated

- **Lookahead bias**: backtest fills use next-bar style execution and configurable latency bars.
- **Data leakage risk**: walk-forward folds are explicit and ordered by time.
- **Unrealistic fills**: cost model includes spread, slippage, fees, and partial-fill constraints.
- **Fragile sizing**: risk manager uses volatility-targeted scaling and stop-distance validation.
- **Weak risk brakes**: confidence threshold + cooldown-by-bars after consecutive losses.
- **Mismatch between research and execution**: shared execution/risk path is used by backtest and paper flow.

### Research-quality additions

- Walk-forward validation utility.
- Train/validation/test splits.
- Parameter sensitivity scans.
- Regime and volatility context in strategy decisions.
- Risk-adjusted ranking (`sortino_like`, `calmar_like`, drawdown-aware score).
- Trade quality diagnostics (payoff ratio, avg win/loss).
- Equity diagnostics (ulcer index, drawdown duration, recovery factor).
- Stability analysis across downsampled timeframe proxies.

## API endpoints

- `GET /health`
- `GET /config`
- `GET /strategy`
- `GET /paper/status`
- `GET /positions`
- `GET /trades`
- `GET /metrics`
- `GET /diagnostics`
- `POST /paper/start?steps=5`
- `POST /paper/stop`
- `POST /backtest/run`
- `POST /backtest/compare`
- `POST /research/walk-forward`
- `POST /research/sensitivity`
- `POST /research/stability`

## Quick start

```bash
cp .env.example .env
make install
make paper
make backtest
make api
```

## Backtest and research workflow (safe default)

1. Tune candidate parameters only on train+validation windows.
2. Evaluate strategy robustness on test folds only.
3. Review risk-adjusted ranking, not raw return alone.
4. Review diagnostics (`payoff_ratio`, `ulcer_index`, drawdown duration).
5. Run extended paper trading before any live-trading consideration.

## Overfitting risk that still remains

- Repeatedly testing many parameter combinations on the same historical sample can still overfit.
- Downsampled timeframe proxies are not a replacement for fully independent market regimes.
- Current dataset is small and synthetic-like; production research requires larger, cleaner market histories.

## External assumptions

- Exchange API support relies on official `ccxt` implementations.
- Cost assumptions are configurable and conservative defaults; tune per symbol/venue.
- Funding/borrow cost model is not implemented yet (spot baseline).

## Live trading status

Live execution remains intentionally stubbed and blocked unless explicitly enabled with:

- `TRADING__LIVE_TRADING_ENABLED=true`
- `TRADING__MODE=live`

## Limitations

- Sample data feed is CSV simulation for deterministic development.
- No websocket streaming yet.
- No persistent storage for fills/metrics runs.
- No exchange min-lot and min-notional metadata validation from market specs yet.

## Next safe steps

1. Add persistent run storage and experiment tracking.
2. Add exchange market-rule validation (lot size, tick size, min notional).
3. Add live feed health checks + stale data circuit breaker.
4. Add larger multi-symbol historical datasets with strict train/validation/test protocol.
5. Add capacity/impact stress tests before live deployment.
