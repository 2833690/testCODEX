# AGENTS.md

## Project rules
- Always start with a short implementation plan before large changes.
- Prefer small, reviewable patches.
- Run tests after each major change.
- Never enable live trading by default.
- Paper trading first, backtesting second, live trading last.
- Never commit secrets or real API keys.
- Ask before adding dependencies outside the approved stack.
- Keep exchange-specific logic isolated from strategy logic.
- Account for fees and slippage in all performance reporting.
- Favor robust risk-adjusted performance over raw return.
- Update README when setup, architecture, or behavior changes.

## Engineering standards
- Use Python type hints.
- Keep modules small and cohesive.
- Make strategy functions pure and testable.
- Make risk checks mandatory before execution.
- Use structured logging.
- Add tests for risk logic and strategy logic.

## Safety defaults
- Live trading must be behind an explicit feature flag.
- Default mode is paper trading.
- No real exchange access in tests.
- Reject trades when risk constraints fail.

## Review guidelines

- Treat lookahead bias, data leakage, unrealistic fills, and missing fee/slippage modeling as P1.
- Treat missing stop-loss enforcement, broken position sizing, and absent drawdown guards as P1.
- Treat silent exception handling in execution, order state, and portfolio accounting as P1.
- Prefer branch + PR workflow; never push directly to main.
- Prefer realistic research quality over flashy strategy complexity.
- Do not approve strategies based only on raw return; emphasize drawdown, expectancy, stability, and robustness.
- Update README when assumptions or runtime behavior change.

- ## Product goals
- Build a trading research and signal platform, not a hype bot.
- Prioritize backtesting realism, paper trading correctness, and operator clarity.
- Signals must be explainable and persisted.
- Risk validation is mandatory before execution.
- Prefer robust risk-adjusted performance over raw return.

## Safety defaults
- Live trading disabled by default.
- No real keys in tests.
- No hidden assumptions about profitability.
- Account for fees, slippage, and realistic execution constraints.

## Engineering rules
- Keep strategies pure and testable.
- Keep exchange adapters isolated.
- Update README when behavior changes.
- Run tests after major changes.
- Use small, reviewable commits.
