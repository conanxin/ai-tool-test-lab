#!/usr/bin/env python3
"""
ATL-5 result validator: validate_atl5_cloud_smoke_result.py

Validates the atl5_cloud_smoke_result.json produced by atl5_cloud_smoke_run.py.

Checks:
- File exists.
- Valid JSON.
- No secret-shaped strings (API key, sk-*, Authorization, Cookie).
- train_samples == 8, eval_samples == 2.
- If launch_succeeded true: run_id non-empty, experiment_url contains app.castform.com.
- Does not modify any file.

Exits 0 on PASS, non-zero on FAIL. Std-lib only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = (
    ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "cloud-smoke-run"
    / "live"
    / "atl5_cloud_smoke_result.json"
)

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Authorization:\s*[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Cookie:\s*[A-Za-z0-9_\-]{20,}"),
]

FORBIDDEN_LITERALS = ["CASTFORM_API_KEY", "castform_api_key", "api_key", "token", "secret", "password"]


def main() -> int:
    print("=" * 60)
    print("ATL-5 result validator")
    print("=" * 60)

    if not RESULT_PATH.exists():
        print(f"[FAIL] result file missing: {RESULT_PATH}")
        return 1
    print(f"[OK]   result file exists: {RESULT_PATH}")

    try:
        text = RESULT_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[FAIL] invalid JSON: {exc}")
        return 1
    print("[OK]   valid JSON")

    # Secret scan
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            print(f"[FAIL] forbidden secret pattern in result JSON: {pat.pattern}")
            return 1
    # Allow the field name "api_key_recorded" (boolean flag, not a secret).
    for lit in FORBIDDEN_LITERALS:
        if lit in text and lit != "api_key":
            print(f"[FAIL] forbidden literal in result JSON: {lit}")
            return 1
    # "api_key" is allowed only as part of "api_key_recorded" (the boolean flag).
    if "api_key" in text and "api_key_recorded" not in text:
        print("[FAIL] forbidden literal 'api_key' in result JSON (outside api_key_recorded)")
        return 1
    print("[OK]   no secret-shaped strings in result JSON")

    # Field checks
    if data.get("train_samples") != 8:
        print(f"[FAIL] train_samples must be 8, got {data.get('train_samples')!r}")
        return 1
    print("[OK]   train_samples == 8")

    if data.get("eval_samples") != 2:
        print(f"[FAIL] eval_samples must be 2, got {data.get('eval_samples')!r}")
        return 1
    print("[OK]   eval_samples == 2")

    if data.get("api_key_recorded") is not False:
        print(f"[FAIL] api_key_recorded must be false, got {data.get('api_key_recorded')!r}")
        return 1
    print("[OK]   api_key_recorded == false")

    if data.get("launch_succeeded") is True:
        run_id = data.get("run_id")
        if not run_id or not isinstance(run_id, str):
            print(f"[FAIL] launch_succeeded=true but run_id missing or empty: {run_id!r}")
            return 1
        print(f"[OK]   run_id present: {run_id}")

        url = data.get("experiment_url", "")
        if "app.castform.com" not in url:
            print(f"[FAIL] experiment_url must contain app.castform.com, got: {url!r}")
            return 1
        print(f"[OK]   experiment_url contains app.castform.com: {url}")

    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
