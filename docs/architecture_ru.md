# Архитектура

Слои: `data -> strategies -> risk -> execution -> paper/backtest -> reports -> ui`.

- `app/data`: загрузка, очистка, версионирование датасетов.
- `app/strategies`: чистые сигнальные модули.
- `app/risk`: обязательные risk-checks.
- `app/backtest`: честный симулятор исполнения и метрики.
- `app/paper`: локальный paper-брокер и восстановление состояния.
- `app/storage`: файловое хранилище JSONL/CSV.
- `ui/`: Streamlit GUI (11 вкладок).
