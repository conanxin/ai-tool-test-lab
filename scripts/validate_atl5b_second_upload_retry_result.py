#!/usr/bin/env python3
"""
ATL-5B validator: validate_atl5b_second_upload_retry_result.py

Validates the atl5b_second_upload_launch_retry_result.json produced by
atl5b_second_upload_launch_retry.py (when the user runs it manually).

Behavior contract:
- If the result JSON does NOT exist, print "SKIPPED_RESULT_NOT_PRESENT"
  and exit 0 (script-prep phase has no result yet; this is expected).
- If the result JSON exists, run the checks below and print PASS or FAIL.
- Std-lib only (json, re, sys, pathlib). No network, no API calls.

Checks performed (when result JSON is present):
- File contains valid JSON.
- No API key / sk-* / Authorization / Cookie / Bearer-shaped strings.
- train_samples == 8.
- eval_samples == 2.
- api_key_recorded == false.
- launcher_args_used does NOT contain batch_size.
- launcher_args_used contains learning_rate.
- If upload_succeeded is true, uploaded_payload_present must be true.
- If launch_succeeded is true, run_id must be a non-empty string.
- If launch_succeeded is true, experiment_url must contain "app.castform.com".

Exits 0 on SKIPPED or PASS, 1 on FAIL.
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
    / "atl5b_second_upload_launch_retry_result.json"
)

# Forbidden secret-shaped patterns.
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Authorization:\s*[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Cookie:\s*[A-Za-z0-9_\-]{20,}"),
]

# Forbidden secret-shaped literals. "api_key" is allowed only as part of
# "api_key_recorded" (the boolean flag, not a secret value).
SECRET_LITERALS = [
    "CASTFORM_API_KEY",
    "castform_api_key",
    "sk-",
    "Bearer ",
    "Authorization:",
    "Cookie:",
]


def main() -> int:
    print("=" * 60)
    print("ATL-5B second upload + launch retry result validator")
    print("=" * 60)

    # 1. Result JSON must exist for non-skip behavior.
    if not RESULT_PATH.exists():
        print("SKIPPED_RESULT_NOT_PRESENT")
        return 0

    # 2. Read & parse.
    try:
        text = RESULT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot read result JSON: {exc}")
        return 1
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        return 1

    failures: list[str] = []

    # 3. No API key / sk- / Authorization / Cookie.
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            failures.append(f"forbidden secret pattern: {pat.pattern}")
    for lit in SECRET_LITERALS:
        if lit in text:
            failures.append(f"forbidden secret literal: {lit!r}")
    # "api_key" is allowed only inside the field name "api_key_recorded".
    if "api_key" in text and "api_key_recorded" not in text:
        failures.append("forbidden literal 'api_key' (outside api_key_recorded)")

    # 4. train_samples == 8.
    if data.get("train_samples") != 8:
        failures.append(f"train_samples must be 8, got {data.get('train_samples')!r}")

    # 5. eval_samples == 2.
    if data.get("eval_samples") != 2:
        failures.append(f"eval_samples must be 2, got {data.get('eval_samples')!r}")

    # 6. api_key_recorded == false.
    if data.get("api_key_recorded") is not False:
        failures.append(
            f"api_key_recorded must be false, got {data.get('api_key_recorded')!r}"
        )

    # 7. launcher_args_used must not contain batch_size.
    launcher_args = data.get("launcher_args_used") or {}
    if not isinstance(launcher_args, dict):
        failures.append(
            f"launcher_args_used must be a dict, got {type(launcher_args).__name__}"
        )
    else:
        if "batch_size" in launcher_args:
            failures.append("launcher_args_used contains forbidden 'batch_size'")
        if "learning_rate" not in launcher_args:
            failures.append("launcher_args_used missing required 'learning_rate'")

    # 8. Conditional checks.
    if data.get("upload_succeeded") is True:
        if data.get("uploaded_payload_present") is not True:
            failures.append(
                "upload_succeeded=true requires uploaded_payload_present=true"
            )

    if data.get("launch_succeeded") is True:
        run_id = data.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            failures.append(
                f"launch_succeeded=true requires non-empty run_id, got {run_id!r}"
            )
        url = data.get("experiment_url") or ""
        if not isinstance(url, str) or "app.castform.com" not in url:
            failures.append(
                f"launch_succeeded=true requires experiment_url containing "
                f"'app.castform.com', got {url!r}"
            )

    # Output.
    if failures:
        print("FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())