#!/usr/bin/env python3
"""
ATL-5A validator: validate_atl5a_launch_args_fix.py

Validates the ATL-5A launch args fix and ATL-5 first run result.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_DIR = ROOT / "cases" / "castform-hermes-phase-closer-v0" / "cloud-smoke-run" / "live"
RESULT_PATH = LIVE_DIR / "atl5_cloud_smoke_result.json"
NOTES_PATH = LIVE_DIR / "ATL5A_LAUNCH_ARGS_FIX_NOTES.md"
GUARD_PATH = LIVE_DIR / "atl5b_second_upload_retry_guard.py"
SCRIPT_PATH = LIVE_DIR / "atl5_cloud_smoke_run.py"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
]

KEY_ASSIGN_RE = re.compile(
    r"""(?ix)
    \b(?:CASTFORM_API_KEY|castform_api_key|api_key|token|secret|password)\b
    \s*=\s*
    ['"](?P<v>[^'"<>\s]{16,})['"]
    """
)


def main() -> int:
    errors: list[str] = []
    checks: list[str] = []

    def ok(msg: str) -> None:
        checks.append(f"[OK]   {msg}")

    def fail(msg: str) -> None:
        errors.append(msg)
        checks.append(f"[FAIL] {msg}")

    # 1. result file exists
    if not RESULT_PATH.exists():
        fail("atl5_cloud_smoke_result.json missing")
        print_result(errors, checks)
        return 1
    ok("atl5_cloud_smoke_result.json exists")

    # 2. valid JSON
    try:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"result JSON invalid: {exc}")
        print_result(errors, checks)
        return 1
    ok("result JSON valid")

    # 3. status check
    status = result.get("status")
    if status != "UPLOAD_DONE_LAUNCH_FAILED":
        fail(f"status expected UPLOAD_DONE_LAUNCH_FAILED, got {status!r}")
    else:
        ok("status == UPLOAD_DONE_LAUNCH_FAILED")

    # 4. upload_succeeded
    if result.get("upload_succeeded") is not True:
        fail(f"upload_succeeded expected true, got {result.get('upload_succeeded')!r}")
    else:
        ok("upload_succeeded == true")

    # 5. launch_succeeded
    if result.get("launch_succeeded") is not False:
        fail(f"launch_succeeded expected false, got {result.get('launch_succeeded')!r}")
    else:
        ok("launch_succeeded == false")

    # 6. error_summary contains batch_size
    error_summary = result.get("error_summary", "")
    if "batch_size" not in error_summary:
        fail(f"error_summary missing 'batch_size': {error_summary!r}")
    else:
        ok("error_summary contains 'batch_size'")

    # 7. uploaded_payload missing (expected known limitation)
    if "uploaded_payload" in result:
        fail("uploaded_payload unexpectedly present in original result (should be missing for first run)")
    else:
        ok("uploaded_payload missing in original result (expected known limitation)")

    # 8. ATL5A_LAUNCH_ARGS_FIX_NOTES.md exists
    if not NOTES_PATH.exists():
        fail("ATL5A_LAUNCH_ARGS_FIX_NOTES.md missing")
    else:
        ok("ATL5A_LAUNCH_ARGS_FIX_NOTES.md exists")

    # 9. atl5b_second_upload_retry_guard.py exists
    if not GUARD_PATH.exists():
        fail("atl5b_second_upload_retry_guard.py missing")
    else:
        ok("atl5b_second_upload_retry_guard.py exists")

    # 10. atl5_cloud_smoke_run.py no longer contains batch_size in launcher_args
    if not SCRIPT_PATH.exists():
        fail("atl5_cloud_smoke_run.py missing")
    else:
        ok("atl5_cloud_smoke_run.py exists")
        script_text = SCRIPT_PATH.read_text(encoding="utf-8")
        # Check for batch_size in launcher_args context
        if '"batch_size"' in script_text or "'batch_size'" in script_text:
            fail("atl5_cloud_smoke_run.py still contains 'batch_size' in launcher_args")
        else:
            ok("atl5_cloud_smoke_run.py no longer contains 'batch_size' in launcher_args")

        # 11. contains learning_rate
        if '"learning_rate"' in script_text or "'learning_rate'" in script_text:
            ok("atl5_cloud_smoke_run.py contains 'learning_rate'")
        else:
            fail("atl5_cloud_smoke_run.py missing 'learning_rate'")

    # 12. secret scan
    for p in [RESULT_PATH, NOTES_PATH, GUARD_PATH, SCRIPT_PATH]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                fail(f"forbidden secret pattern in {p.name}: {pat.pattern}")
        for m in KEY_ASSIGN_RE.finditer(text):
            fail(f"key-like assignment in {p.name}: variable assigned {m.group('v')[:4]}... (redacted)")

    if not any("forbidden secret" in e or "key-like assignment" in e for e in errors):
        ok("no secret-shaped strings in checked files")

    print_result(errors, checks)
    return 1 if errors else 0


def print_result(errors: list[str], checks: list[str]) -> None:
    print("=" * 60)
    print("ATL-5A launch args fix validator")
    print("=" * 60)
    for line in checks:
        print(line)
    print()
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        for e in errors:
            print(f"  - {e}")
    else:
        print("RESULT: PASS")


if __name__ == "__main__":
    sys.exit(main())
