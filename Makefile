.PHONY: install test api paper backtest

install:
	pip install -e .[dev]

test:
	pytest

api:
	uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

paper:
	python scripts/run_paper.py

backtest:
	python scripts/run_backtest.py
