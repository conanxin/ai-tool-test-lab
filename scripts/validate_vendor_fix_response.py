#!/usr/bin/env python3
"""ATL-RESUME-1 vendor fix response validator (Python stdlib only).

Verifies the ATL-RESUME-1 Castform vendor fix response bundle is properly recorded:

  * VENDOR_FIX_RESPONSE.md exists
  * the new status tag `VENDOR_FIX_RECEIVED_RETEST_PENDING` appears
  * the vendor-confirmed root cause phrase `raw data dict` appears
  * the credit update phrase `$100` (or `$100 in extra credits`) appears
  * data/cases.json has Castform case final_status == "VENDOR_FIX_RECEIVED_RETEST_PENDING"
  * CASE_CLOSEOUT.md still preserves the historical closeout status
    `PAUSED_PENDING_CASTFORM_BACKEND_LOGS` (audit trail invariant)
  * both run_id tokens still appear (historical evidence preserved)
  * files do not contain API keys, sk-* style keys, Authorization headers,
    cookies, or key-like private tokens (16 secret patterns + 1 forbidden
    literal scan; the forbidden literal is built at runtime via chr-concat
    so the validator source itself does not contain the bare pattern — see
    pitfall #27 in the ai-tool-test-lab SKILL).

Exits 0 on PASS, 1 on FAIL. Outputs PASS/FAIL line plus detailed reason list.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "castform-hermes-phase-closer-v0"
REPORT_DIR = REPO_ROOT / "reports"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

VENDOR_FIX_FILE = CASE_DIR / "VENDOR_FIX_RESPONSE.md"
CASE_CLOSEOUT_FILE = CASE_DIR / "CASE_CLOSEOUT.md"
SUPPORT_REQUEST_FILE = CASE_DIR / "CASTFORM_SUPPORT_REQUEST_FINAL.md"
RESUME1_REPORT_FILE = REPORT_DIR / "ATL_RESUME1_CASTFORM_VENDOR_FIX_RESPONSE_REPORT.md"

RUN_ID_RUN1 = "c83f971d-2b2c-42b8-9774-ca64938c1286"
RUN_ID_RUN2 = "56cb5701-6b3e-424e-b671-fc2efc932aa8"

# Status tag for the new phase.
NEW_STATUS_TAG = "VENDOR_FIX_RECEIVED_RETEST_PENDING"
# Status tag for the historical closeout (must still appear in CASE_CLOSEOUT.md).
HISTORICAL_STATUS_TAG = "PAUSED_PENDING_CASTFORM_BACKEND_LOGS"

EXPECTED_CASE_PHASE = "VENDOR-FIX-RECEIVED"
EXPECTED_CASE_STATUS = "vendor fix received; retest pending"
EXPECTED_CASE_FINAL_STATUS = "VENDOR_FIX_RECEIVED_RETEST_PENDING"

# 16 secret patterns mirrored from the ATL-CLOSEOUT validator for consistency.
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

# Forbidden-literal scan: built at runtime via chr-concat so the validator source
# itself does not contain the bare key-prefix pattern (per pitfall #27).
SECRET_LITERALS = (
    "cf" + "_" + "J",
)


def _check_file(path: Path, must_contain: list) -> list:
    issues = []
    if not path.exists():
        issues.append(f"missing file: {path}")
        return issues
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"unreadable file {path}: {exc}")
        return issues
    for needle in must_contain:
        if needle not in text:
            issues.append(f"{path.name}: missing required token: {needle!r}")
    for pat in SECRET_PATTERNS:
        match = pat.search(text)
        if match:
            issues.append(
                f"{path.name}: secret-shaped match for pattern {pat.pattern!r}: <REDACTED_SECRET_LITERAL>"
            )
    for literal in SECRET_LITERALS:
        if literal in text:
            issues.append(
                f"{path.name}: contains forbidden secret literal: {literal!r}"
            )
    return issues


def _check_cases_json() -> list:
    issues = []
    if not CASES_JSON.exists():
        issues.append(f"missing file: {CASES_JSON}")
        return issues
    try:
        raw = CASES_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"unreadable or invalid json {CASES_JSON}: {exc}")
        return issues
    cases = data.get("cases", [])
    castform = None
    for c in cases:
        if c.get("slug") == "castform-hermes-phase-closer-v0":
            castform = c
            break
    if castform is None:
        issues.append("cases.json: no case with slug castform-hermes-phase-closer-v0")
        return issues
    if castform.get("phase") != EXPECTED_CASE_PHASE:
        issues.append(
            f"cases.json: Castform case phase != {EXPECTED_CASE_PHASE!r} "
            f"(got {castform.get('phase')!r})"
        )
    if castform.get("status") != EXPECTED_CASE_STATUS:
        issues.append(
            f"cases.json: Castform case status != {EXPECTED_CASE_STATUS!r} "
            f"(got {castform.get('status')!r})"
        )
    if castform.get("final_status") != EXPECTED_CASE_FINAL_STATUS:
        issues.append(
            f"cases.json: Castform case final_status != {EXPECTED_CASE_FINAL_STATUS!r} "
            f"(got {castform.get('final_status')!r})"
        )
    if not castform.get("canonical_example", False):
        issues.append("cases.json: Castform case canonical_example must remain True")
    if not castform.get("workflow_reference", False):
        issues.append("cases.json: Castform case workflow_reference must remain True")
    # secret-pattern scan on raw bytes
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            issues.append(
                f"cases.json: secret-shaped match for pattern {pat.pattern!r}"
            )
    for literal in SECRET_LITERALS:
        if literal in raw:
            issues.append(
                f"cases.json: contains forbidden secret literal: {literal!r}"
            )
    return issues


def main() -> int:
    issues = []

    if not CASE_DIR.exists():
        issues.append(f"missing case dir: {CASE_DIR}")
    if not REPORT_DIR.exists():
        issues.append(f"missing report dir: {REPORT_DIR}")

    # VENDOR_FIX_RESPONSE.md: must exist + new status + root cause phrase + $100 credits
    issues.extend(_check_file(
        VENDOR_FIX_FILE,
        [
            NEW_STATUS_TAG,
            "raw data dict",
            "$100",
            RUN_ID_RUN1,
            RUN_ID_RUN2,
        ],
    ))

    # CASE_CLOSEOUT.md: must still preserve historical closeout status + both run_ids
    issues.extend(_check_file(
        CASE_CLOSEOUT_FILE,
        [
            HISTORICAL_STATUS_TAG,
            NEW_STATUS_TAG,
            RUN_ID_RUN1,
            RUN_ID_RUN2,
        ],
    ))

    # CASTFORM_SUPPORT_REQUEST_FINAL.md: both run_ids still present
    issues.extend(_check_file(
        SUPPORT_REQUEST_FILE,
        [RUN_ID_RUN1, RUN_ID_RUN2],
    ))

    # Resume-1 report: must mention new status tag (light check)
    issues.extend(_check_file(
        RESUME1_REPORT_FILE,
        [NEW_STATUS_TAG],
    ))

    # cases.json structural + field-level checks
    issues.extend(_check_cases_json())

    if issues:
        print("FAIL: validate_vendor_fix_response")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS: validate_vendor_fix_response")
    print(f"  - VENDOR_FIX_RESPONSE.md exists and contains all required tokens")
    print(f"  - new status tag present in doc + cases.json: {NEW_STATUS_TAG}")
    print(f"  - historical closeout status still preserved in CASE_CLOSEOUT.md: {HISTORICAL_STATUS_TAG}")
    print(f"  - vendor-confirmed root cause phrase present: raw data dict")
    print(f"  - credit update phrase present: $100")
    print(f"  - both run_id tokens preserved: {RUN_ID_RUN1} + {RUN_ID_RUN2}")
    print(f"  - data/cases.json Castform case phase: {EXPECTED_CASE_PHASE}")
    print(f"  - data/cases.json Castform case status: {EXPECTED_CASE_STATUS}")
    print(f"  - data/cases.json Castform case final_status: {EXPECTED_CASE_FINAL_STATUS}")
    print(f"  - canonical_example and workflow_reference preserved")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns, {len(SECRET_LITERALS)} literals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
