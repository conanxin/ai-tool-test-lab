#!/usr/bin/env python3
"""
prepare_starter_style_subset.py — ATL-6A starter-style subset preparation.

Reads the first 16 rows of cases/castform-hermes-phase-closer-v0/sample-train.jsonl
and the first 4 rows of sample-eval.jsonl, then writes them to:

  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-train.preview.jsonl
  cases/castform-hermes-phase-closer-v0/starter-style-redeploy/starter-eval.preview.jsonl

This is intentionally a pure stdlib script:
  * no network
  * no Castform API
  * no upload
  * no training
  * no LLM judge

It only re-slices the existing ATL-2 redacted JSONL samples into a slightly
larger subset (16 train / 4 eval) than the ATL-5 smoke subset (8 train / 2 eval).

Hard rules respected:
  * the file never reads, prints, or records CASTFORM_API_KEY
  * the file does not call benchmax.cloud.client.TrainerClient
  * the file does not invoke upload_training_run or launch_training_run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = REPO_ROOT / "cases" / "castform-hermes-phase-closer-v0"
OUT_DIR = Path(__file__).resolve().parent

SOURCE_TRAIN = CASE_DIR / "sample-train.jsonl"
SOURCE_EVAL = CASE_DIR / "sample-eval.jsonl"

OUT_TRAIN = OUT_DIR / "starter-train.preview.jsonl"
OUT_EVAL = OUT_DIR / "starter-eval.preview.jsonl"

TRAIN_COUNT = 16
EVAL_COUNT = 4

REQUIRED_KEYS = ("prompt", "ground_truth")


def _validate_row(row: dict, *, line_no: int, source: Path) -> None:
    if not isinstance(row, dict):
        raise ValueError(
            f"{source.name}:{line_no}: row is not a JSON object: {type(row).__name__}"
        )
    missing = [k for k in REQUIRED_KEYS if k not in row]
    if missing:
        raise ValueError(
            f"{source.name}:{line_no}: missing required keys: {missing}; "
            f"got keys: {sorted(row.keys())}"
        )
    if not isinstance(row["prompt"], str) or not row["prompt"].strip():
        raise ValueError(
            f"{source.name}:{line_no}: 'prompt' is empty or not a string"
        )
    if not isinstance(row["ground_truth"], str):
        raise ValueError(
            f"{source.name}:{line_no}: 'ground_truth' is not a string: "
            f"{type(row['ground_truth']).__name__}"
        )


def _slice(source: Path, n: int, out: Path) -> int:
    if not source.exists():
        raise FileNotFoundError(f"source JSONL not found: {source}")
    written = 0
    with source.open("r", encoding="utf-8") as fin, out.open(
        "w", encoding="utf-8"
    ) as fout:
        for line_no, raw in enumerate(fin, start=1):
            if written >= n:
                break
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line, strict=False)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{source.name}:{line_no}: invalid JSON: {exc}"
                ) from exc
            _validate_row(row, line_no=line_no, source=source)
            fout.write(
                json.dumps(
                    {
                        "prompt": row["prompt"],
                        "ground_truth": row["ground_truth"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ATL-6A starter-style subset preparation (stdlib only)."
    )
    parser.add_argument(
        "--train-count", type=int, default=TRAIN_COUNT, help="train rows to keep"
    )
    parser.add_argument(
        "--eval-count", type=int, default=EVAL_COUNT, help="eval rows to keep"
    )
    args = parser.parse_args()

    print(f"=== ATL-6A prepare_starter_style_subset ===")
    print(f"source train: {SOURCE_TRAIN}")
    print(f"source eval : {SOURCE_EVAL}")
    print(f"out train   : {OUT_TRAIN}")
    print(f"out eval    : {OUT_EVAL}")
    print(
        "no network · no API key · no upload · no training · no LLM judge"
    )

    n_train = _slice(SOURCE_TRAIN, args.train_count, OUT_TRAIN)
    n_eval = _slice(SOURCE_EVAL, args.eval_count, OUT_EVAL)

    print(f"--- result ---")
    print(f"train written: {n_train} (target {args.train_count})")
    print(f"eval written : {n_eval} (target {args.eval_count})")
    if n_train < args.train_count:
        print(
            f"WARN: source train had only {n_train} rows; output has {n_train}"
        )
    if n_eval < args.eval_count:
        print(
            f"WARN: source eval had only {n_eval} rows; output has {n_eval}"
        )
    if n_train != args.train_count or n_eval != args.eval_count:
        return 2
    print("PASS: starter-style subset prepared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
