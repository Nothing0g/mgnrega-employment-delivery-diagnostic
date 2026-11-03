"""SQLite persistence for validated aggregate panels; source files stay local."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


def write_sqlite(frame: pd.DataFrame, database: str | Path, metadata: dict) -> None:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        frame.to_sql("district_panel", connection, if_exists="replace", index=False)
        pd.DataFrame([{"metadata_json": json.dumps(metadata, ensure_ascii=False)}]).to_sql(
            "ingest_metadata", connection, if_exists="replace", index=False
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_panel_fy_state ON district_panel (fy, state)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_panel_district ON district_panel (district)")
        connection.commit()
