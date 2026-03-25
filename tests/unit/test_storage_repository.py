from pathlib import Path

from app.storage.repository import SqliteRepository


def test_repository_persists_runs_signals_and_events(tmp_path: Path) -> None:
    repo = SqliteRepository(str(tmp_path / 'platform.db'))

    run_id = repo.save_run('backtest', 'ema_crossover', 'BTC/USDT', '1m', {'final_equity': 10010})
    signal_id = repo.save_signal(
        {
            'strategy_name': 'ema_crossover',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'signal_type': 'entry',
            'confidence': 0.8,
            'reason': 'fast_above_slow',
            'explanation': 'Trend up',
            'key_features': {'fast_ema': 101.0, 'slow_ema': 100.0},
            'stop_loss': 99.0,
            'take_profit': 105.0,
            'stop_loss_basis': 'ATR',
            'invalidation_condition': 'crossdown',
        },
        timeframe='1m',
    )
    trade_id = repo.save_trade(
        {
            'symbol': 'BTC/USDT',
            'side': 'sell',
            'quantity': 1.0,
            'entry_price': 100.0,
            'exit_price': 101.0,
            'pnl': 1.0,
            'fee': 0.1,
            'timestamp': 1700000000,
        }
    )
    event_id = repo.save_event('entry', 'filled', {'symbol': 'BTC/USDT'})

    assert run_id > 0
    assert signal_id > 0
    assert trade_id > 0
    assert event_id > 0
    assert len(repo.list_runs(run_type='backtest')) == 1
    assert len(repo.list_signals()) == 1
    assert len(repo.list_trades()) == 1
    assert len(repo.list_events()) == 1
