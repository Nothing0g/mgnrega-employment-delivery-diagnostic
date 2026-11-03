from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgnrega_diag.ingest import read_source  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a government portal export before explicitly mapping its headers.")
    parser.add_argument("file", help="Local CSV or Excel source file.")
    args = parser.parse_args()
    path = Path(args.file)
    frame = read_source(path)
    print(f"File: {path.name}")
    print(f"SHA-256: {hashlib.sha256(path.read_bytes()).hexdigest()}")
    print(f"Rows: {len(frame):,}")
    print("Exact source headers:")
    for column in frame.columns:
        print(f"  - {column}")
    print("\nFirst five rows (review for aggregate-only content before use):")
    print(frame.head().to_string(index=False))
    print("\nNo field mappings were inferred. Record each source definition before canonicalizing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
