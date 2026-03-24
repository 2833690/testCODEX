# Reliable Crypto Bot (Paper First)

Production-minded algorithmic trading framework for Binance (default) with adapter-ready architecture for Bybit.

## Safety-first defaults

- **Default mode: paper trading**.
- **Live trading is feature-flagged and disabled by default**.
- No secrets in code. Use environment variables from `.env`.
- Backtests account for **fees, spread, slippage, latency, and partial fills**.
- Strategy metrics are evaluated after costs.
- All entry orders pass through mandatory risk checks.

## Architecture

```text
app/
  api/            FastAPI endpoints
  config/         Pydantic settings and validation
  core/           Bot composition and orchestration
  exchange/       CCXT + simulation adapters
  data/           OHLCV loading, validation, feed abstraction
  strategies/     Pure strategy modules (no exchange calls)
  risk/           Mandatory pre-trade risk checks and sizing
  execution/      Signal -> order translation
  portfolio/      Portfolio/account state
  backtest/       Bar-by-bar backtesting and metrics/ranking
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

## Major realism improvements (second pass)

- Backtest execution now uses **next-bar execution semantics** with configurable bar latency to reduce lookahead bias.
- Costs model includes fee + spread + slippage + partial fill ratio.
- Risk layer adds confidence gate, minimum stop distance gate, cooldown-by-bars after loss streak, and volatility-targeted position sizing.
- Strategy context includes regime and volatility signals to stabilize entries.
- Metrics now include `sortino_like` and `calmar_like` and ranking emphasizes risk-adjusted robustness.

## Quick start

1. Copy env:

```bash
cp .env.example .env
```

2. Install:

```bash
make install
```

3. Run paper trading CLI:

```bash
make paper
```

4. Run API:

```bash
make api
```

5. Run backtest and strategy ranking:

```bash
make backtest
```

6. Run tests:

```bash
make test
```

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

## Backtest and research workflow

- Use walk-forward split utility (`train`, `validation`, `test`) and evaluate on test set after selecting parameters on train/validation only.
- Re-run strategy comparison with different periods and symbols and prioritize stable ranking, not one-run max return.
- Keep paper trading enabled by default and require extended paper burn-in before any live deployment.

## External assumptions

- Exchange API support relies on official `ccxt` exchange implementations.
- Trading cost assumptions are configurable and intentionally conservative defaults; adapt per symbol and venue.
- No funding-rate model yet (spot-first baseline).

## Overfitting and leakage warnings

- Repeated parameter tuning on one holdout can overfit even with walk-forward splits.
- Never use future bars for signal generation or fill simulation.
- Keep strict separation between model selection and final out-of-sample evaluation.

## Docker

```bash
docker compose up --build
```

## Live trading status

Live execution remains intentionally stubbed and blocked unless explicitly enabled with:

- `TRADING__LIVE_TRADING_ENABLED=true`
- `TRADING__MODE=live`

## Limitations

- Sample data feed is CSV-based simulation for deterministic development.
- No websocket streaming yet; polling abstraction is websocket-ready.
- No persistence DB yet for long-running production audit trails.
- No funding or borrow cost model (spot baseline only).

## Next safe steps

1. Add persistent storage (orders, fills, equity curve, risk events).
2. Add websocket feed with reconnect/backoff and data quality checks.
3. Add regime-specific parameter sensitivity report and stability score.
4. Add exchange lot-size/min-notional filters from market metadata.
5. Add long-duration paper-run health checks and circuit-breaker alerts.
