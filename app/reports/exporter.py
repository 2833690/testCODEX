from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class ReportExporter:
    def __init__(self, reports_dir: str = "storage/reports") -> None:
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, report_name: str, payload: dict[str, Any]) -> Path:
        path = self.reports_dir / f"{report_name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def export_csv(self, report_name: str, rows: list[dict[str, Any]]) -> Path:
        path = self.reports_dir / f"{report_name}.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def export_html(self, report_name: str, title: str, sections: dict[str, Any]) -> Path:
        body = "".join([f"<h2>{k}</h2><pre>{json.dumps(v, ensure_ascii=False, indent=2)}</pre>" for k, v in sections.items()])
        html = f"<html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1>{body}</body></html>"
        path = self.reports_dir / f"{report_name}.html"
        path.write_text(html, encoding="utf-8")
        return path
