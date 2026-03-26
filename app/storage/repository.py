from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LocalFileRepository:
    """Файловое хранилище событий/сигналов/сделок без внешней БД."""

    def __init__(self, storage_dir: str = "storage") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._json_files = {
            "runs": self.storage_dir / "runs.jsonl",
            "signals": self.storage_dir / "signals.jsonl",
            "trades": self.storage_dir / "trades.jsonl",
            "events": self.storage_dir / "events.jsonl",
        }
        self._csv_files = {
            "runs": self.storage_dir / "runs.csv",
            "signals": self.storage_dir / "signals.csv",
            "trades": self.storage_dir / "trades.csv",
            "events": self.storage_dir / "events.csv",
        }
        self._counters_path = self.storage_dir / "counters.json"
        self._ensure_files()

    def _ensure_files(self) -> None:
        for path in list(self._json_files.values()) + list(self._csv_files.values()):
            if not path.exists():
                path.touch()
        if not self._counters_path.exists():
            self._counters_path.write_text(json.dumps({"runs": 0, "signals": 0, "trades": 0, "events": 0}))

    def _next_id(self, key: str) -> int:
        counters = json.loads(self._counters_path.read_text())
        counters[key] += 1
        self._counters_path.write_text(json.dumps(counters))
        return int(counters[key])

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    @staticmethod
    def _append_csv(path: Path, row: dict[str, Any]) -> None:
        existing_header = path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size > 0 else None
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if existing_header is None:
                writer.writeheader()
            writer.writerow(row)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def save_run(self, run_type: str, strategy: str, symbol: str, timeframe: str, payload: dict[str, Any]) -> int:
        row = {
            "id": self._next_id("runs"),
            "run_type": run_type,
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "created_at": self._now_iso(),
            "payload": payload,
        }
        self._append_jsonl(self._json_files["runs"], row)
        self._append_csv(self._csv_files["runs"], {**row, "payload": json.dumps(payload, ensure_ascii=False)})
        return int(row["id"])

    def list_runs(self, run_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self._json_files["runs"])
        if run_type:
            rows = [r for r in rows if r["run_type"] == run_type]
        return rows[-max(1, limit) :][::-1]

    def save_signal(self, payload: dict[str, Any], timeframe: str) -> int:
        row = {
            "id": self._next_id("signals"),
            "strategy": payload.get("strategy_name", "unknown"),
            "symbol": payload["symbol"],
            "timeframe": timeframe,
            "signal_type": payload["signal_type"],
            "side": payload["side"],
            "confidence": float(payload.get("confidence", 0.0)),
            "reason": payload.get("reason", ""),
            "explanation": payload.get("explanation", ""),
            "key_features": payload.get("key_features", {}),
            "stop_loss": payload.get("stop_loss"),
            "take_profit": payload.get("take_profit"),
            "stop_loss_basis": payload.get("stop_loss_basis", ""),
            "invalidation_condition": payload.get("invalidation_condition", ""),
            "created_at": self._now_iso(),
        }
        self._append_jsonl(self._json_files["signals"], row)
        self._append_csv(self._csv_files["signals"], {**row, "key_features": json.dumps(row["key_features"], ensure_ascii=False)})
        return int(row["id"])

    def list_signals(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._read_jsonl(self._json_files["signals"])[-max(1, limit) :][::-1]

    def save_trade(self, trade: dict[str, Any]) -> int:
        row = {
            "id": self._next_id("trades"),
            "symbol": trade["symbol"],
            "side": trade["side"],
            "quantity": float(trade["quantity"]),
            "entry_price": float(trade["entry_price"]),
            "exit_price": float(trade["exit_price"]),
            "pnl": float(trade["pnl"]),
            "fee": float(trade["fee"]),
            "timestamp_ms": int(trade["timestamp"]),
        }
        self._append_jsonl(self._json_files["trades"], row)
        self._append_csv(self._csv_files["trades"], row)
        return int(row["id"])

    def list_trades(self, limit: int = 200) -> list[dict[str, Any]]:
        return self._read_jsonl(self._json_files["trades"])[-max(1, limit) :][::-1]

    def save_event(self, event_type: str, status: str, details: dict[str, Any]) -> int:
        row = {
            "id": self._next_id("events"),
            "event_type": event_type,
            "status": status,
            "details": details,
            "created_at": self._now_iso(),
        }
        self._append_jsonl(self._json_files["events"], row)
        self._append_csv(self._csv_files["events"], {**row, "details": json.dumps(details, ensure_ascii=False)})
        return int(row["id"])

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        return self._read_jsonl(self._json_files["events"])[-max(1, limit) :][::-1]


# backward-compatible alias
SqliteRepository = LocalFileRepository
