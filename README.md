# Локальная платформа исследования и автоматизации крипто-стратегий

Платформа для локального исследования рынка, бэктестов, walk-forward анализа, paper trading и безопасного auto/live execution (live по умолчанию отключен).

## Что реализовано
- Полностью локальная работа: файлы в `storage/` (JSON/CSV/Parquet), без PostgreSQL/MySQL/Redis.
- Data layer: импорт CSV, очистка, нормализация символов, версионирование датасетов, ресемплинг.
- Стратегии: `Trend Following Breakout`, `Mean Reversion`, `Volatility Breakout`, `Regime Filter`.
- Честный backtest с next-bar исполнением, fee/slippage/spread/latency/partial fill.
- Optimization и research API: split, walk-forward, sensitivity, stability.
- Risk engine с обязательными pre-trade проверками.
- Paper trading с restart-safe хранением в файлах.
- GUI на Streamlit (11 вкладок).
- Экспорт отчётов в JSON/CSV/HTML.

## Быстрый запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
streamlit run ui/streamlit_app.py
```

API:
```bash
uvicorn app.api.main:app --reload
```

## Ключевая безопасность
- Режим по умолчанию: `paper`.
- `live` разрешается только при явном флаге.
- Платформа не обещает прибыль и не использует “AI magic”.

## Документация (RU)
См. `docs/*.md`.
