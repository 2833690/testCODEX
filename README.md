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
- **Signal loss under latency**: pending signals are queued and executed only when their latency window matures (no overwrite on later bars).
- **Fragile sizing**: risk manager uses volatility-targeted scaling and stop-distance validation.
- **Weak risk brakes**: confidence threshold + cooldown-by-bars after consecutive losses.
- **Mismatch between research and execution**: shared execution/risk path is used by backtest and paper flow.
- Protective stop-loss/take-profit checks are applied on each new bar before signal processing.
- **Accounting correctness**: portfolio equity now marks open positions to market value, and realized trade PnL includes both entry and exit fees.
- **Cost realism**: execution prices apply bid/ask side selection (buy at ask, sell at bid), then slippage and fee modeling.
- **Deterministic auditability**: backtest/paper fills use candle timestamps for trade records instead of wall-clock timestamps.

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

- `GET /` (redirects to `/ui`)
- `GET /ui` (built-in web console for paper/backtest/research actions)
- `GET /ui/assets/*` (static JS/CSS for the web console)
- `GET /health`
- `GET /config`
- `GET /strategies`
- `GET /strategy`
- `GET /market/latest`
- `GET /signals/latest`
- `GET /signals/history`
- `GET /signals/persisted`
- `GET /paper/status`
- `GET /paper/runs`
- `GET /positions`
- `GET /trades`
- `GET /metrics`
- `GET /diagnostics`
- `GET /events/audit`
- `POST /paper/start?steps=5`
- `POST /paper/stop`
- `POST /backtest/run`
- `GET /backtest/results`
- `GET /reports/backtests/export?format=json|csv`
- `POST /backtest/compare`
- `POST /research/split`
- `POST /research/walk-forward`
- `POST /research/sensitivity`
- `POST /research/stability`

All endpoints return dashboard-friendly envelopes:
`{"status":"ok","message":"...","data":{...}}`.

The built-in web console (`/ui`) calls these same endpoints so operators can run paper trading, backtests, and diagnostics directly from a browser without writing custom frontend code.

## Quick start

```bash
cp .env.example .env
make install
make paper
make backtest
make api
```

For local/CI test runs, install the package first and then test dependencies:

```bash
pip install -e .
pip install -e ".[test]"
pytest
```

## Backtest and research workflow (safe default)

1. Tune candidate parameters only on train+validation windows.
2. Evaluate strategy robustness on test folds only.
3. Review risk-adjusted ranking, not raw return alone.
4. Review diagnostics (`payoff_ratio`, `ulcer_index`, drawdown duration).
5. Run extended paper trading before any live-trading consideration.

## Operator workflow (paper-first)

1. Configure `.env` from `.env.example` and keep `TRADING__MODE=paper`.
2. Run `make backtest` and review:
   - risk-adjusted metrics,
   - drawdown diagnostics,
   - trade/streak distribution,
   - regime performance breakdown.
3. Run `make paper` and monitor:
   - `/signals/latest`, `/signals/persisted`,
   - `/diagnostics`,
   - `/events/audit`.
4. Export run history with `/reports/backtests/export?format=csv` for comparison.

## Persistence and explainability

- Runs, signals, trades, and execution audit events are persisted in SQLite (`STORAGE__SQLITE_PATH`).
- Each entry/exit signal carries:
  - strategy name,
  - direction,
  - confidence,
  - key trigger features,
  - stop-loss basis,
  - invalidation condition,
  - short human-readable explanation.

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

### Mandatory pre-live validation checklist (not implemented as automatic approval)

- Validate exchange lot/tick/min-notional enforcement against real market metadata.
- Validate persistent order lifecycle reconciliation and recovery after restarts.
- Validate kill-switch and circuit-breaker behavior in failure drills.
- Validate timeout/retry behavior against exchange outage and partial connectivity.
- Validate cost model assumptions (fees/slippage/spread/funding) on production-like data.
- Validate capacity/impact limits and drawdown controls in prolonged paper runs.

## Limitations

- Sample data feed is CSV simulation for deterministic development.
- No websocket streaming yet.
- No exchange min-lot and min-notional metadata validation from market specs yet.
- Latency is modeled in bars, not milliseconds; microstructure-level queue position is not modeled.
- Partial-fill model is heuristic and not yet based on order book depth snapshots.
- Funding, borrow costs, and overnight financing are still not modeled.

## Next safe steps

1. Add exchange market-rule validation (lot size, tick size, min notional).
2. Add live feed health checks + stale data circuit breaker.
3. Add larger multi-symbol historical datasets with strict train/validation/test protocol.
4. Add capacity/impact stress tests before live deployment.
5. Add richer trade-duration analytics from event-level data.


## Deployment readiness assessment

- **Safe for research:** Yes, with conservative assumptions and explicit overfitting warnings.
- **Safe for paper trading:** Yes, for controlled dry runs; monitor diagnostics and rejected-trade logs.
- **Not safe for live trading yet:** Yes. Missing exchange rule enforcement, persistent audit trail, and deeper market-impact/funding modeling.
