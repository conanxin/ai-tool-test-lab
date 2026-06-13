#!/usr/bin/env python3
"""
ATL-4B-CONFIG: prepare_cloud_smoke_subset.py

Dry subset extractor for the future Castform cloud smoke run.

- Reads the first N rows from sample-train.jsonl and sample-eval.jsonl
  (defaults: 8 train, 2 eval — matches cloud_smoke_config.json).
- Writes preview-only JSONL files in this directory.
- Files are named with the .preview.jsonl suffix to make clear they are
  NOT the final upload artifacts.
- Uses Python std-lib only. No network. No Castform API.
- Does not import upload_training_run, launch_training_run, or TrainerClient.

This script is allowed by the ATL-4B-CONFIG hard boundaries because it
does NOT call the Castform API and does NOT upload anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAIN_SRC = HERE.parent / "sample-train.jsonl"
EVAL_SRC = HERE.parent / "sample-eval.jsonl"

TRAIN_OUT = HERE / "smoke-train.preview.jsonl"
EVAL_OUT = HERE / "smoke-eval.preview.jsonl"

# Must match cloud_smoke_config.json. Hard-coded as a safety cross-check.
EXPECTED_TRAIN = 8
EXPECTED_EVAL = 2


def take_n(src: Path, n: int) -> list[dict]:
    rows: list[dict] = []
    with src.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"[FAIL] {src.name} line {i + 1} is not valid JSON: {exc}"
                )
            rows.append(obj)
            if len(rows) >= n:
                break
    return rows


def write_preview(rows: list[dict], out: Path, expected: int) -> None:
    if len(rows) != expected:
        raise SystemExit(
            f"[FAIL] expected {expected} rows for {out.name}, got {len(rows)}"
        )
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False))
            fh.write("\n")
    print(f"[OK] wrote {len(rows)} rows -> {out}")


def main() -> int:
    if not TRAIN_SRC.exists():
        print(f"[FAIL] missing {TRAIN_SRC}", file=sys.stderr)
        return 1
    if not EVAL_SRC.exists():
        print(f"[FAIL] missing {EVAL_SRC}", file=sys.stderr)
        return 1

    print("[INFO] ATL-4B-CONFIG prepare_cloud_smoke_subset.py")
    print("[INFO] dry subset extraction only — no API, no upload, no training")

    train_rows = take_n(TRAIN_SRC, EXPECTED_TRAIN)
    eval_rows = take_n(EVAL_SRC, EXPECTED_EVAL)

    write_preview(train_rows, TRAIN_OUT, EXPECTED_TRAIN)
    write_preview(eval_rows, EVAL_OUT, EXPECTED_EVAL)

    print("[OK] preview subset prepared; files are .preview.jsonl (not for upload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
