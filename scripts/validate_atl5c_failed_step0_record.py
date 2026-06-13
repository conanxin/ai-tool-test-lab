#!/usr/bin/env python3
"""
ATL-5C validator: validate_atl5c_failed_step0_record.py

Validates the ATL-5C failure-record scaffolding (md + script) and
that none of the recorded files contain real key fragments or
sensitive literal strings.

Checks:
- cases/.../monitoring/atl5c-first-run-failed-step0.md exists
- cases/.../monitoring/atl5c-failure-diagnostics-template.md exists
- cases/.../monitoring/atl5c_readonly_status_probe.py exists
- run_id `c83f971d-2b2c-42b8-9774-ca64938c1286` appears in the md record
- actual UI URL appears in the md record
- the md record mentions `failed`, `step 0`, and `no rollouts` (or near
  equivalents)
- no `sk-<...>` key-like fragment
- no `cf_<...>` key-like fragment
- no `Authorization:` header literal
- no `Cookie:` header literal

The probe script is allowed to contain `cf-` (with hyphen) as part of
its regex pattern list — that is an intentional sentinel, not a real
key. We only flag `cf_` (with underscore) which is the actual Castform
key prefix. The probe script is also checked for any long
alphanumeric run that looks like a leaked key, but is exempt from
the regex-literal scan.

Exits 0 on PASS, 1 on FAIL. Std-lib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MONITORING = (
    ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "cloud-smoke-run"
    / "monitoring"
)
RECORD_MD = MONITORING / "atl5c-first-run-failed-step0.md"
TEMPLATE_MD = MONITORING / "atl5c-failure-diagnostics-template.md"
PROBE_PY = MONITORING / "atl5c_readonly_status_probe.py"

RUN_ID = "c83f971d-2b2c-42b8-9774-ca64938c1286"
ACTUAL_UI_URL = (
    "https://app.castform.com/train/c83f971d-2b2c-42b8-9774-ca64938c1286?tab=train"
)

# Secret-shaped literal patterns. We deliberately do NOT scan for the
# probe script's `cf-` regex literals — those are sentinels, not leaks.
SECRET_LITERALS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"cf_[A-Za-z0-9]{16,}"),
    re.compile(r"Authorization:\s*[A-Za-z0-9_\-]{8,}"),
    re.compile(r"Cookie:\s*[A-Za-z0-9_\-]{8,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]{20,}"),
]

# Phrases the record md must contain (case-insensitive contains).
REQUIRED_PHRASES = (
    "failed",
    "step 0",
    "no rollouts",
    RUN_ID,
    ACTUAL_UI_URL,
    "FAILED_STEP_0_NO_ROLLOUTS",
)


def main() -> int:
    print("=" * 64)
    print("ATL-5C failure-record validator")
    print("=" * 64)

    errors: list[str] = []
    checks: list[str] = []

    def ok(msg: str) -> None:
        checks.append(f"[OK]   {msg}")

    def fail(msg: str) -> None:
        errors.append(msg)
        checks.append(f"[FAIL] {msg}")

    # 1. file existence
    for label, p in (
        ("record md", RECORD_MD),
        ("template md", TEMPLATE_MD),
        ("probe script", PROBE_PY),
    ):
        if p.exists():
            ok(f"{label} exists: {p.relative_to(ROOT)}")
        else:
            fail(f"{label} missing: {p.relative_to(ROOT)}")

    if not RECORD_MD.exists():
        return _finish(errors, checks)

    text = RECORD_MD.read_text(encoding="utf-8")
    lower = text.lower()

    # 2. required phrases
    for phrase in REQUIRED_PHRASES:
        if phrase.lower() in lower:
            ok(f"record md contains: {phrase!r}")
        else:
            fail(f"record md missing required phrase: {phrase!r}")

    # 3. secret-shape literal scan (record md)
    for pat in SECRET_LITERALS:
        if pat.search(text):
            fail(f"forbidden secret literal in record md: {pat.pattern}")
    if not any("forbidden secret" in e for e in errors):
        ok("no forbidden secret literal in record md")

    # 4. secret-shape literal scan (template md)
    if TEMPLATE_MD.exists():
        t_text = TEMPLATE_MD.read_text(encoding="utf-8")
        for pat in SECRET_LITERALS:
            if pat.search(t_text):
                fail(f"forbidden secret literal in template md: {pat.pattern}")
        if not any("forbidden secret" in e for e in errors):
            ok("no forbidden secret literal in template md")

    # 5. probe script — basic sanity (compile + has read-only verb list)
    if PROBE_PY.exists():
        p_text = PROBE_PY.read_text(encoding="utf-8")
        try:
            compile(p_text, str(PROBE_PY), "exec")
            ok("probe script compiles (syntax OK)")
        except SyntaxError as exc:
            fail(f"probe script syntax error: {exc}")
        for required_symbol in (
            "READ_ONLY_PREFIXES",
            "DESTRUCTIVE_KEYWORDS",
            "NO_READ_ONLY_STATUS_METHOD_FOUND",
            "_scrub",
        ):
            if required_symbol in p_text:
                ok(f"probe script contains required symbol: {required_symbol}")
            else:
                fail(f"probe script missing required symbol: {required_symbol}")
        for pat in SECRET_LITERALS:
            if pat.search(p_text):
                fail(
                    f"forbidden secret literal in probe script: {pat.pattern} "
                    "(probe script should use only regex sentinels, not "
                    "literal key shapes)"
                )
        if not any("forbidden secret" in e for e in errors):
            ok("no forbidden secret literal in probe script")

    return _finish(errors, checks)


def _finish(errors, checks):
    for line in checks:
        print(line)
    print()
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
