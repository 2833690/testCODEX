from app.backtest.diagnostics import (
    metrics_by_symbol_timeframe,
    regime_performance_breakdown,
    streak_analysis,
    trade_distribution_analysis,
)
from app.models.trading import TradeRecord


def sample_trades() -> list[TradeRecord]:
    return [
        TradeRecord(order_id='1', symbol='BTC/USDT', side='sell', quantity=1, entry_price=100, exit_price=101, pnl=1, fee=0.1, timestamp=1),
        TradeRecord(order_id='2', symbol='BTC/USDT', side='sell', quantity=1, entry_price=101, exit_price=99, pnl=-2, fee=0.1, timestamp=2),
        TradeRecord(order_id='3', symbol='BTC/USDT', side='sell', quantity=1, entry_price=99, exit_price=102, pnl=3, fee=0.1, timestamp=3),
    ]


def test_trade_distribution_and_streaks() -> None:
    trades = sample_trades()
    dist = trade_distribution_analysis(trades)
    streaks = streak_analysis(trades)
    assert 'pnl_p50' in dist
    assert streaks['longest_loss_streak'] >= 1


def test_metrics_and_regime_breakdown() -> None:
    trades = sample_trades()
    metrics = metrics_by_symbol_timeframe(trades, timeframe='1m')
    assert 'BTC/USDT|1m' in metrics

    signals = [
        {'signal_type': 'entry', 'regime': 'bull'},
        {'signal_type': 'exit', 'regime': 'bear'},
        {'signal_type': 'entry', 'regime': 'bull'},
    ]
    breakdown = regime_performance_breakdown(signals, trades)
    assert 'bull' in breakdown or 'bear' in breakdown
