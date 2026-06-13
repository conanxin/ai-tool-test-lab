#!/usr/bin/env python3
"""
validate_starter_style_env.py — ATL-6A local validate_env (stdlib contract).

Exercises benchmax.platform.validation.validate_env against
HermesPhaseCloserStarterStyleEnv with:
  * local=True
  * api_key=None
  * no upload
  * no training
  * no Castform API call

Inputs:
  starter-train.preview.jsonl (first 5 rows)
  starter-eval.preview.jsonl (first 2 rows)

Output:
  VALIDATE_ENV_LOCAL_PASS  — on success
  VALIDATE_ENV_LOCAL_FAIL: <reason>  — on failure

Hard rules respected:
  * no Castform API
  * no upload
  * no training
  * no network
  * no API key
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from benchmax.platform.validation import validate_env

THIS_DIR = Path(__file__).resolve().parent
TRAIN_FILE = THIS_DIR / "starter-train.preview.jsonl"
EVAL_FILE = THIS_DIR / "starter-eval.preview.jsonl"


def _first_n_rows(path: Path, n: int) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if len(rows) >= n:
                break
    return rows


def main() -> int:
    print("=== ATL-6A validate_starter_style_env ===")
    print(f"train file: {TRAIN_FILE}")
    print(f"eval file : {EVAL_FILE}")
    print("no network · no API key · no upload · no training")

    if not TRAIN_FILE.exists():
        print(f"VALIDATE_ENV_LOCAL_FAIL: missing {TRAIN_FILE.name}")
        return 1
    if not EVAL_FILE.exists():
        print(f"VALIDATE_ENV_LOCAL_FAIL: missing {EVAL_FILE.name}")
        return 1

    train_rows = _first_n_rows(TRAIN_FILE, 5)
    eval_rows = _first_n_rows(EVAL_FILE, 2)
    print(f"train rows used: {len(train_rows)} (target 5)")
    print(f"eval rows used : {len(eval_rows)} (target 2)")

    if len(train_rows) < 5:
        print(
            f"VALIDATE_ENV_LOCAL_FAIL: only {len(train_rows)} train rows; "
            f"need 5"
        )
        return 1
    if len(eval_rows) < 2:
        print(
            f"VALIDATE_ENV_LOCAL_FAIL: only {len(eval_rows)} eval rows; "
            f"need 2"
        )
        return 1

    # Local-only contract check.
    from environment_starter_style import HermesPhaseCloserStarterStyleEnv

    try:
        result = validate_env(
            env_class=HermesPhaseCloserStarterStyleEnv,
            env_args={},
            train_dataset=train_rows,
            eval_dataset=eval_rows,
            local=True,
            api_key=None,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"VALIDATE_ENV_LOCAL_FAIL: {type(exc).__name__}: {exc}")
        return 1

    print(f"validate_env returned: {type(result).__name__}")
    print(f"result: {result}")

    if getattr(result, "local_failed", 1) == 0 and getattr(
        result, "local_passed", 0
    ) > 0:
        print(
            f"VALIDATE_ENV_LOCAL_PASS "
            f"(local {result.local_passed}/{result.local_passed + result.local_failed} checks)"
        )
        return 0
    print(
        f"VALIDATE_ENV_LOCAL_FAIL: local_passed={getattr(result, 'local_passed', '?')} "
        f"local_failed={getattr(result, 'local_failed', '?')}"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
