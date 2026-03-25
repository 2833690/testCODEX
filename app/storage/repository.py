from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SqliteRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    side TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    key_features_json TEXT NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    stop_loss_basis TEXT NOT NULL,
                    invalidation_condition TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    pnl REAL NOT NULL,
                    fee REAL NOT NULL,
                    timestamp_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS execution_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_run(self, run_type: str, strategy: str, symbol: str, timeframe: str, payload: dict[str, Any]) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs(run_type, strategy, symbol, timeframe, payload_json) VALUES (?, ?, ?, ?, ?)",
                (run_type, strategy, symbol, timeframe, json.dumps(payload)),
            )
            return int(cur.lastrowid)

    def list_runs(self, run_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        q = "SELECT * FROM runs"
        params: list[Any] = []
        if run_type:
            q += " WHERE run_type = ?"
            params.append(run_type)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(q, params).fetchall()
        return [self._row_with_payload(r) for r in rows]

    def save_signal(self, payload: dict[str, Any], timeframe: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO signals(strategy, symbol, timeframe, signal_type, side, confidence, reason, explanation,
                    key_features_json, stop_loss, take_profit, stop_loss_basis, invalidation_condition)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get("strategy_name", "unknown"),
                    payload["symbol"],
                    timeframe,
                    payload["signal_type"],
                    payload["side"],
                    float(payload["confidence"]),
                    payload.get("reason", ""),
                    payload.get("explanation", ""),
                    json.dumps(payload.get("key_features", {})),
                    payload.get("stop_loss"),
                    payload.get("take_profit"),
                    payload.get("stop_loss_basis", ""),
                    payload.get("invalidation_condition", ""),
                ),
            )
            return int(cur.lastrowid)

    def list_signals(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_with_features(r) for r in rows]

    def save_trade(self, trade: dict[str, Any]) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO trades(symbol, side, quantity, entry_price, exit_price, pnl, fee, timestamp_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    trade["symbol"],
                    trade["side"],
                    float(trade["quantity"]),
                    float(trade["entry_price"]),
                    float(trade["exit_price"]),
                    float(trade["pnl"]),
                    float(trade["fee"]),
                    int(trade["timestamp"]),
                ),
            )
            return int(cur.lastrowid)

    def list_trades(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def save_event(self, event_type: str, status: str, details: dict[str, Any]) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO execution_events(event_type, status, details_json) VALUES (?, ?, ?)",
                (event_type, status, json.dumps(details)),
            )
            return int(cur.lastrowid)

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM execution_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(r), "details": json.loads(r["details_json"])} for r in rows]

    @staticmethod
    def _row_with_payload(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json"))
        return data

    @staticmethod
    def _row_with_features(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["key_features"] = json.loads(data.pop("key_features_json"))
        return data
