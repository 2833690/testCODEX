.PHONY: install test api paper backtest gui

install:
	pip install -e .
	pip install -e ".[dev,test]"

test:
	pytest

api:
	uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

gui:
	streamlit run ui/streamlit_app.py

paper:
	python scripts/run_paper.py

backtest:
	python scripts/run_backtest.py
