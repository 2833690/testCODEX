# Reliable Crypto Bot (Paper First)

Production-minded algorithmic trading framework for Binance (default) with adapter-ready architecture for Bybit.

## Safety-first defaults

- **Default mode: paper trading**.
- **Live trading is feature-flagged and disabled by default**.
- No secrets in code. Use environment variables from `.env`.
- Backtests include **fees and slippage**.
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
  strategies/     Pure strategy modules
  risk/           Mandatory pre-trade risk checks
  execution/      Signal -> order translation
  portfolio/      Portfolio/account state
  backtest/       Bar-by-bar backtesting and metrics
  paper/          Paper broker and paper job orchestration
  models/         Shared typed domain objects
  utils/          Logging and indicator helpers
tests/
  unit/
  integration/
scripts/
  run_paper.py
  run_backtest.py
```

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
- `POST /paper/start?steps=5`
- `POST /paper/stop`
- `POST /backtest/run`

## Profitability research notes

- Compare EMA crossover, mean reversion, and breakout in backtests via `scripts/run_backtest.py`.
- Ranking emphasizes risk-adjusted return (Sharpe-like, drawdown, and net return), not raw return only.
- Walk-forward split utility exists (`train`, `validation`, `test`) to reduce data snooping.
- **Overfitting risk** still exists when repeatedly tuning on the same validation/test sets; rotate out-of-sample periods and maintain strict holdout data.

## Docker

```bash
docker compose up --build
```

## Live trading status

Live execution interface is intentionally stubbed and blocked unless explicitly enabled with `TRADING__LIVE_TRADING_ENABLED=true` and `TRADING__MODE=live`.

## Assumptions and limitations

- Sample data feed is CSV-based simulation for deterministic development.
- No websocket streaming yet; polling abstraction is websocket-ready.
- No persistence DB yet for long-running production audit trails.
- Exchange adapter retries network/timeouts only.

## Next safe steps

1. Add persistent storage (orders, fills, equity curve, risk events).
2. Add websocket feed with reconnect/backoff.
3. Add richer slippage model (volume-aware) and realistic latency model.
4. Add stricter exposure controls (per-symbol/per-sector budgets).
5. Add out-of-sample rolling retraining and parameter stability checks.
