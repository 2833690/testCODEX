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
