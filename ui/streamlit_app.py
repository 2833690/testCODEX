from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app.api.main import (
    diagnostics,
    export_backtests,
    list_audit_events,
    list_backtest_results,
    paper_status,
    persisted_signals,
    run_backtest,
    start_paper,
)
from app.config.settings import get_settings
from app.data.dataset_manager import DatasetManager
from app.reports import ReportExporter
from app.strategies.registry import STRATEGY_BUILDERS

st.set_page_config(page_title="Локальная крипто-платформа", page_icon="📈", layout="wide")
st.title("📈 Локальная платформа исследований и paper trading")
settings = get_settings()
dataset_manager = DatasetManager(settings.storage.datasets_dir)
exporter = ReportExporter(settings.storage.reports_dir)

tabs = st.tabs([
    "Dashboard", "Market Data", "Strategies", "Backtest", "Optimization", "Paper Trading",
    "Live Trading", "Risk Monitor", "Reports", "Settings", "Logs"
])

with tabs[0]:
    st.subheader("Сводка")
    d = diagnostics()["data"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Сделок", d["trade_count"])
    c2.metric("Точек equity", d["equity_points"])
    c3.metric("Consecutive losses", d["risk_state"]["consecutive_losses"])

with tabs[1]:
    st.subheader("Данные рынка")
    uploaded = st.file_uploader("Импорт CSV (timestamp,open,high,low,close,volume)", type=["csv"])
    symbol = st.text_input("Символ", value=settings.strategy.symbol)
    tf = st.selectbox("Таймфрейм", ["1m", "5m", "15m", "1h", "4h", "1d"], index=0)
    if uploaded is not None and st.button("Импортировать CSV"):
        temp = Path("storage") / "tmp_upload.csv"
        temp.parent.mkdir(exist_ok=True)
        temp.write_bytes(uploaded.getvalue())
        ref = dataset_manager.import_csv(str(temp), symbol, tf)
        st.success(f"Импортировано: {ref.path}")

with tabs[2]:
    st.subheader("Стратегии")
    rows = []
    for name, cls in STRATEGY_BUILDERS.items():
        obj = cls()
        rows.append({"strategy": name, "описание": getattr(obj, "description_ru", ""), "params": json.dumps(obj.config(), ensure_ascii=False)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tabs[3]:
    st.subheader("Backtest")
    if st.button("Запустить backtest"):
        result = run_backtest()["data"]
        st.json(result)
    results = list_backtest_results()["data"]["persisted"]
    if results:
        table = pd.DataFrame([{"created_at": r["created_at"], "strategy": r["strategy"], "equity": r["payload"].get("final_equity", 0)} for r in results])
        st.dataframe(table, use_container_width=True)
        fig = px.line(table.iloc[::-1], y="equity", title="Equity curve по запускам")
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("Optimization")
    st.info("Grid/Random/Walk-forward доступны через API: /research/sensitivity, /research/walk-forward, /research/split")

with tabs[5]:
    st.subheader("Paper trading")
    steps = st.slider("Количество шагов", 1, 50, 5)
    if st.button("Запустить paper trading"):
        st.json(start_paper(steps=steps))
    st.json(paper_status())

with tabs[6]:
    st.subheader("Live trading")
    st.error("⚠️ Live trading по умолчанию отключен. Включайте только явным флагом и после расширенного paper-run.")

with tabs[7]:
    st.subheader("Risk monitor")
    st.json(diagnostics()["data"]["risk_state"])

with tabs[8]:
    st.subheader("Reports")
    backtests = list_backtest_results()["data"]["persisted"]
    if st.button("Экспортировать summary отчёт"):
        path_json = exporter.export_json("summary_report", {"backtests": backtests})
        path_csv = exporter.export_csv("backtest_report", [{"id": r["id"], "strategy": r["strategy"], "equity": r["payload"].get("final_equity", 0)} for r in backtests])
        path_html = exporter.export_html("daily_strategy_report", "Ежедневный отчёт", {"backtests": backtests[:10]})
        st.success(f"Создано: {path_json}, {path_csv}, {path_html}")

with tabs[9]:
    st.subheader("Settings")
    st.json(settings.model_dump(exclude={"api_key", "api_secret"}))

with tabs[10]:
    st.subheader("Logs")
    st.dataframe(pd.DataFrame(list_audit_events()["data"]["events"]), use_container_width=True)
    st.dataframe(pd.DataFrame(persisted_signals()["data"]["signals"]), use_container_width=True)
