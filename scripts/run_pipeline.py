from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgnrega_diag.ingest import read_source, validate_panel  # noqa: E402
from mgnrega_diag.metrics import add_metrics  # noqa: E402
from mgnrega_diag.storage import write_sqlite  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and process a local canonical MGNREGA district-year extract.")
    parser.add_argument("--input", required=True, help="Local CSV or Excel file that you have mapped to the canonical schema.")
    parser.add_argument("--out-dir", default="data/processed", help="Output directory (git-ignored by default).")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        parser.error(f"Input file not found: {source}")
    raw = read_source(source)
    result = validate_panel(raw)
    print(f"Rows read: {len(raw)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 2

    enriched = add_metrics(result.data)
    synthetic = (
        "synthetic" in source.stem.lower()
        or (
            result.data["state"].astype(str).str.startswith("TEST-").all()
            and result.data["district"].astype(str).str.startswith("Test District").all()
        )
    )
    if synthetic:
        print("WARNING: Synthetic test input detected; all derived outputs remain synthetic and must not be used as government findings.")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "district_panel.csv"
    database_path = out_dir / "mgnrega_diagnostic.sqlite"
    metadata_path = out_dir / "ingest_metadata.json"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    metadata = {
        "source_filename": source.name,
        "source_sha256": digest,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": int(len(enriched)),
        "financial_years": sorted(enriched["fy"].dropna().astype(str).unique().tolist()),
        "states": int(enriched["state"].nunique(dropna=True)),
        "districts": int(enriched["district"].nunique(dropna=True)),
        "warnings": result.warnings,
        "synthetic": synthetic,
        "note": (
            "Synthetic software-test records; not government data."
            if synthetic
            else "The file is user-supplied. Verify its government source, metric labels, coverage and period before interpreting it."
        ),
    }
    enriched.to_csv(csv_path, index=False)
    write_sqlite(enriched, database_path, metadata)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Processed CSV: {csv_path}")
    print(f"SQLite database: {database_path}")
    print(f"Metadata: {metadata_path}")
    print("No input records were added to version control by this pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
