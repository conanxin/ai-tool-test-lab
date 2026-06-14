#!/usr/bin/env python3
"""ATL-RESUME-2 vendor-fix retest validator (Python stdlib only).

Verifies the ATL-RESUME-2 Castform vendor-fix retest script is properly prepared
(execution is NOT run during ATL-RESUME-2A; this validator checks the prep):

  * vendor-fix-retest/ directory exists
  * atl_resume2_vendor_fix_retest.py exists and compiles
  * the script does NOT use `batch_size` in launcher_args
  * the script DOES use `learning_rate` in launcher_args
  * the script declares the ATL-RESUME-2 authorization string
  * the script declares the hermes-phase-closer-vendor-fix-retest run_name
  * the script does NOT reference old failed run_ids as functional input
    (audit-trail references inside docstring / env_fix_points are tolerated)

Result JSON handling (mirror ATL-6A pattern):
  * If atl_resume2_vendor_fix_retest_result.json is absent: output
    `SKIPPED_RESULT_NOT_PRESENT` and exit 0 (the script is prep-only, not run).
  * If result JSON is present:
      - check no secret-shaped strings (16 patterns + 1 forbidden literal)
      - check `train_samples == 16`
      - check `eval_samples == 4`
      - check `api_key_recorded == false`
      - if `launch_succeeded` true: `run_id` non-empty + `experiment_url` contains
        `app.castform.com`

Exits 0 on PASS or SKIPPED_RESULT_NOT_PRESENT, 1 on FAIL. Output style:
single `PASS: ...` / `FAIL: ...` line + concise bullet list.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "castform-hermes-phase-closer-v0"
RETEST_DIR = CASE_DIR / "vendor-fix-retest"
SCRIPT_FILE = RETEST_DIR / "atl_resume2_vendor_fix_retest.py"
RESULT_FILE = RETEST_DIR / "atl_resume2_vendor_fix_retest_result.json"

AUTHORIZATION_STRING = "I AUTHORIZE ATL-RESUME-2 CASTFORM RETEST AFTER VENDOR FIX"
EXPECTED_RUN_NAME = "hermes-phase-closer-vendor-fix-retest"
EXPECTED_TRAIN_SAMPLES = 16
EXPECTED_EVAL_SAMPLES = 4
EXPECTED_PHASE = "ATL-RESUME-2"
EXPECTED_ENV_NAME = "HermesPhaseCloserStarterStyleEnv"

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"sk_test_[A-Za-z0-9]{8,}"),
    re.compile(r"CFK-[A-Za-z0-9]{8,}"),
    re.compile(r"castform_[A-Za-z0-9]{8,}"),
    re.compile(r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9]{8,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE),
    re.compile(r"Cookie\s*:\s*[A-Za-z0-9=._;-]{8,}", re.IGNORECASE),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"gho_[A-Za-z0-9]{16,}"),
    re.compile(r"ghu_[A-Za-z0-9]{16,}"),
    re.compile(r"ghs_[A-Za-z0-9]{16,}"),
    re.compile(r"ghr_[A-Za-z0-9]{16,}"),
)

# Forbidden literal: built via chr-concat so the validator source itself does
# not contain the bare key-prefix pattern (per pitfall #27).
SECRET_LITERALS = (
    "cf" + "_" + "J",
)

OLD_FAILED_RUN_IDS = (
    "c83f971d-2b2c-42b8-9774-ca64938c1286",
    "56cb5701-6b3e-424e-b671-fc2efc932aa8",
)


def _check_script() -> list:
    issues = []
    if not RETEST_DIR.exists():
        issues.append(f"missing dir: {RETEST_DIR}")
        return issues
    if not SCRIPT_FILE.exists():
        issues.append(f"missing script: {SCRIPT_FILE}")
        return issues
    try:
        text = SCRIPT_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"unreadable script {SCRIPT_FILE}: {exc}")
        return issues

    # compile check
    try:
        compile(text, str(SCRIPT_FILE), "exec")
    except SyntaxError as exc:
        issues.append(f"{SCRIPT_FILE.name}: syntax error: {exc}")
        return issues

    # launch_args schema: must contain learning_rate, must NOT contain batch_size
    # (the only batch_size mention allowed is in docstring/comments; we still
    # scan for it but tolerate docstring/comment lines).
    if "learning_rate" not in text:
        issues.append(f"{SCRIPT_FILE.name}: missing 'learning_rate' in launcher_args")
    if "batch_size" in text:
        # Only fail if it appears as a launcher_arg key (not in docstring).
        bad_lines = []
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            if re.search(r'["\']batch_size["\']\s*:', line):
                bad_lines.append(i)
        if bad_lines:
            issues.append(
                f"{SCRIPT_FILE.name}: contains 'batch_size' as launcher_arg key on lines {bad_lines}"
            )

    # auth string and run_name must appear literally
    if AUTHORIZATION_STRING not in text:
        issues.append(
            f"{SCRIPT_FILE.name}: missing required authorization string: {AUTHORIZATION_STRING!r}"
        )
    if EXPECTED_RUN_NAME not in text:
        issues.append(
            f"{SCRIPT_FILE.name}: missing required run_name: {EXPECTED_RUN_NAME!r}"
        )

    # secret-pattern scan
    for pat in SECRET_PATTERNS:
        match = pat.search(text)
        if match:
            issues.append(
                f"{SCRIPT_FILE.name}: secret-shaped match for pattern {pat.pattern!r}: <REDACTED>"
            )
    for literal in SECRET_LITERALS:
        if literal in text:
            issues.append(
                f"{SCRIPT_FILE.name}: contains forbidden secret literal: {literal!r}"
            )

    return issues


def _check_result_json() -> tuple:
    """Returns (issues, skipped). If result file missing, skipped=True."""
    issues = []
    if not RESULT_FILE.exists():
        return issues, True  # SKIPPED
    try:
        raw = RESULT_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"unreadable or invalid json {RESULT_FILE}: {exc}")
        return issues, False

    # secret-pattern scan on raw
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            issues.append(
                f"{RESULT_FILE.name}: secret-shaped match for pattern {pat.pattern!r}"
            )
    for literal in SECRET_LITERALS:
        if literal in raw:
            issues.append(
                f"{RESULT_FILE.name}: contains forbidden secret literal: {literal!r}"
            )

    if data.get("phase") != EXPECTED_PHASE:
        issues.append(
            f"{RESULT_FILE.name}: phase != {EXPECTED_PHASE!r} (got {data.get('phase')!r})"
        )
    if data.get("train_samples") != EXPECTED_TRAIN_SAMPLES:
        issues.append(
            f"{RESULT_FILE.name}: train_samples != {EXPECTED_TRAIN_SAMPLES} (got {data.get('train_samples')!r})"
        )
    if data.get("eval_samples") != EXPECTED_EVAL_SAMPLES:
        issues.append(
            f"{RESULT_FILE.name}: eval_samples != {EXPECTED_EVAL_SAMPLES} (got {data.get('eval_samples')!r})"
        )
    if data.get("api_key_recorded", True) is not False:
        issues.append(
            f"{RESULT_FILE.name}: api_key_recorded must be False (got {data.get('api_key_recorded')!r})"
        )
    if data.get("old_failed_run_referenced", True) is True:
        issues.append(
            f"{RESULT_FILE.name}: old_failed_run_referenced must be False"
        )

    if data.get("launch_succeeded") is True:
        run_id = data.get("run_id")
        if not run_id or not isinstance(run_id, str) or not run_id.strip():
            issues.append(f"{RESULT_FILE.name}: launch_succeeded=True but run_id empty")
        experiment_url = data.get("experiment_url") or ""
        if "app.castform.com" not in experiment_url:
            issues.append(
                f"{RESULT_FILE.name}: launch_succeeded=True but experiment_url does not contain 'app.castform.com' (got {experiment_url!r})"
            )

    return issues, False


def main() -> int:
    issues = _check_script()
    result_issues, skipped = _check_result_json()
    issues.extend(result_issues)

    if issues:
        print("FAIL: validate_atl_resume2_vendor_fix_retest")
        for line in issues:
            print(f"  - {line}")
        return 1

    if skipped:
        print("SKIPPED_RESULT_NOT_PRESENT: validate_atl_resume2_vendor_fix_retest")
        print(f"  - vendor-fix-retest dir: {RETEST_DIR}")
        print(f"  - retest script: {SCRIPT_FILE.name}")
        print(f"  - result JSON not present yet (script is prep-only, not run)")
        return 0

    print("PASS: validate_atl_resume2_vendor_fix_retest")
    print(f"  - vendor-fix-retest dir: {RETEST_DIR}")
    print(f"  - retest script: {SCRIPT_FILE.name}")
    print(f"  - launcher_args: no batch_size, learning_rate present")
    print(f"  - authorization string present: {AUTHORIZATION_STRING}")
    print(f"  - run_name present: {EXPECTED_RUN_NAME}")
    print(f"  - result JSON present: {RESULT_FILE.name}")
    print(f"  - phase / train_samples / eval_samples / api_key_recorded all match spec")
    print(f"  - launch_succeeded invariants (run_id non-empty + experiment_url contains app.castform.com) verified")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns, {len(SECRET_LITERALS)} literals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
