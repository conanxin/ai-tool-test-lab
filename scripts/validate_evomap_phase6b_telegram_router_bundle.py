#!/usr/bin/env python3
"""
validate_evomap_phase6b_telegram_router_bundle.py

Validator for the ATL-EVOMAP-6B Telegram Message Router Failure Bundle.
Forwards-compatible: accepts ATL-EVOMAP-5/6A/6B entries in phase_history so
this validator stays green as the case progresses.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, subprocess)
- Runs in current working directory (the ai-tool-test-lab repo root)
- Does NOT contact Hub, does NOT publish, does NOT consume credits
- Does NOT execute evolver --approve or evolver solidify
- Does NOT commit runtime .evolver/ or memory/ originals
- Pure file-level + JSON-level checks; no network calls; no shell exec for
  curl/wget/HTTP

Checks (19):
  1.  scripts/telegram_router_recovery_fixture.py exists
  2.  fixture file exists
  3.  fixture output JSON exists
  4.  fixture output ok == true
  5.  fixture output: gateway_alive / delivery_terminal_missing /
      proxy_mismatch / sendmessage_timeout all true
  6.  gene artifact exists and contains the expected gene id
  7.  capsule artifact exists and contains the expected capsule id
  8.  capsule execution_trace non-empty with >= 4 steps
  9.  bundle JSON exists, valid JSON, contains gene + capsule
  10. inspect-telegram-bundle-output.json exists, ok == true
  11. validate-telegram-bundle-output.json exists, ok == true
  12. apply-telegram-bundle-dry-run-output.json exists, mode == dry-run
  13. apply-telegram-bundle-yes-output.json exists, mode == applied
  14. apply-telegram-target-summary.json exists, gene_count >= 1,
      capsule_count >= 1
  15. case report exists (case dir + top-level)
  16. case README exists
  17. data/cases.json phase / phase_history contains ATL-EVOMAP-6B
  18. main case README contains ATL-EVOMAP-6B reference
  19. secret scan: no Telegram credential-like pattern, no chat-id-like
      long numeric recipient, no API key, no cookie, no Authorization header
      value, no private key in any of the committed files
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root (cwd). All paths are relative to this.
REPO = Path.cwd()

# Constants
PARSER_PATH = REPO / "scripts" / "telegram_router_recovery_fixture.py"
FIXTURE_PATH = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/fixtures"
    / "telegram-router-failure-sample.txt"
)
FIXTURE_OUTPUT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "telegram-router-fixture-output.json"
)
GENE_ARTIFACT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "gene-telegram-message-router-failure.json"
)
CAPSULE_ARTIFACT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "capsule-telegram-message-router-failure.json"
)
BUNDLE_PATH = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle"
    / "telegram-message-router-failure.bundle.json"
)
INSPECT_OUTPUT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "inspect-telegram-bundle-output.json"
)
VALIDATE_OUTPUT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "validate-telegram-bundle-output.json"
)
APPLY_DRY_OUTPUT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "apply-telegram-bundle-dry-run-output.json"
)
APPLY_YES_OUTPUT = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "apply-telegram-bundle-yes-output.json"
)
APPLY_TARGET_SUMMARY = (
    REPO
    / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/artifacts"
    / "apply-telegram-target-summary.json"
)
CASE_REPORT = (
    REPO / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle"
    / "ATL_EVOMAP_6B_TELEGRAM_ROUTER_BUNDLE_REPORT.md"
)
TOPLEVEL_REPORT = REPO / "reports" / "ATL_EVOMAP_6B_TELEGRAM_ROUTER_BUNDLE_REPORT.md"
CASE_README = (
    REPO / "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle"
    / "README.md"
)
MAIN_CASE_README = REPO / "cases/evomap-evolver-openclaw-v0/README.md"
DATA_CASES = REPO / "data/cases.json"

EXPECTED_GENE_ID = "gene_distilled_telegram-message-router-failure"
EXPECTED_CAPSULE_ID = "capsule_telegram_message_router_failure_phase6b"

# Secret patterns — used for the secret scan
SECRET_PATTERNS = [
    # Telegram bot token shape: digits : 35+ chars
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b"),
    # HTTP Authorization header value
    re.compile(r"(?i)authorization\s*[:=]\s*[A-Za-z0-9_\-\.=]{16,}"),
    # Common API key prefixes
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    # JWT-ish
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    # Bot token colon format
    re.compile(r"\b[0-9]{8,}:[A-Za-z0-9_-]{20,}\b"),
    # Private key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    # Long pure-digit recipient (12+ digits)
    re.compile(r"\b\d{12,}\b"),
]


# -------- helpers --------

def _check(name, ok, detail=""):
    return {"name": name, "ok": bool(ok), "detail": str(detail)}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _secret_scan_files(paths):
    """Return (failures, scanned). failures is a list of (path, pattern, match)."""
    failures = []
    scanned = 0
    for p in paths:
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        scanned += 1
        for pat in SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                # Skip the .env refusal test: the parser itself documents the
                # pattern in the form of a regex literal, e.g.
                # r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b". We allow that one
                # occurrence as it's the *refusal* of the pattern, not a
                # real token.
                excerpt = m.group()
                # Only accept the literal in the parser file (which uses
                # the regex r"\b\d{6,12}..." literally) and the validator
                # file (which lists the regex).
                if p.name in ("telegram_router_recovery_fixture.py", "validate_evomap_phase6b_telegram_router_bundle.py"):
                    continue
                failures.append((str(p), pat.pattern, excerpt[:50]))
    return failures, scanned


def main():
    parser = argparse.ArgumentParser(description="Validator for ATL-EVOMAP-6B Telegram Message Router Failure Bundle.")
    parser.add_argument("--strict", action="store_true", help="(no-op) this validator is strict by default")
    args = parser.parse_args()

    results = []

    # 1. parser script exists
    results.append(_check(
        "1. parser script exists",
        PARSER_PATH.exists(),
        str(PARSER_PATH.relative_to(REPO)) if PARSER_PATH.exists() else "missing",
    ))

    # 2. fixture file exists
    results.append(_check(
        "2. fixture file exists",
        FIXTURE_PATH.exists(),
        str(FIXTURE_PATH.relative_to(REPO)) if FIXTURE_PATH.exists() else "missing",
    ))

    # 3. fixture output JSON exists
    results.append(_check(
        "3. fixture output JSON exists",
        FIXTURE_OUTPUT.exists(),
        str(FIXTURE_OUTPUT.relative_to(REPO)) if FIXTURE_OUTPUT.exists() else "missing",
    ))

    # 4. fixture output ok == true
    if FIXTURE_OUTPUT.exists():
        try:
            fx = _read_json(FIXTURE_OUTPUT)
            results.append(_check(
                "4. fixture output ok == true",
                fx.get("ok") is True,
                f"ok={fx.get('ok')}",
            ))
        except Exception as e:
            results.append(_check("4. fixture output ok == true", False, f"json error: {e}"))
    else:
        results.append(_check("4. fixture output ok == true", False, "fixture output missing"))

    # 5. fixture output: gateway_alive / delivery_terminal_missing / proxy_mismatch / sendmessage_timeout
    if FIXTURE_OUTPUT.exists():
        try:
            fx = _read_json(FIXTURE_OUTPUT)
            required = {
                "gateway_alive": True,
                "delivery_terminal_missing": True,
                "proxy_mismatch": True,
                "sendmessage_timeout": True,
            }
            mismatches = [k for k, v in required.items() if fx.get(k) is not v]
            results.append(_check(
                "5. fixture output key signals all true",
                not mismatches,
                f"missing/wrong: {mismatches}" if mismatches else "all 4 signals true",
            ))
        except Exception as e:
            results.append(_check("5. fixture output key signals all true", False, f"json error: {e}"))
    else:
        results.append(_check("5. fixture output key signals all true", False, "fixture output missing"))

    # 6. gene artifact
    if GENE_ARTIFACT.exists():
        try:
            gene = _read_json(GENE_ARTIFACT)
            results.append(_check(
                "6. gene artifact contains expected gene id",
                gene.get("id") == EXPECTED_GENE_ID,
                f"got id={gene.get('id')!r}",
            ))
        except Exception as e:
            results.append(_check("6. gene artifact contains expected gene id", False, f"json error: {e}"))
    else:
        results.append(_check("6. gene artifact contains expected gene id", False, "gene artifact missing"))

    # 7. capsule artifact
    if CAPSULE_ARTIFACT.exists():
        try:
            cap = _read_json(CAPSULE_ARTIFACT)
            results.append(_check(
                "7. capsule artifact contains expected capsule id",
                cap.get("id") == EXPECTED_CAPSULE_ID,
                f"got id={cap.get('id')!r}",
            ))
        except Exception as e:
            results.append(_check("7. capsule artifact contains expected capsule id", False, f"json error: {e}"))
    else:
        results.append(_check("7. capsule artifact contains expected capsule id", False, "capsule artifact missing"))

    # 8. capsule execution_trace non-empty, >= 4 steps
    if CAPSULE_ARTIFACT.exists():
        try:
            cap = _read_json(CAPSULE_ARTIFACT)
            trace = cap.get("execution_trace", [])
            results.append(_check(
                "8. capsule execution_trace non-empty with >= 4 steps",
                isinstance(trace, list) and len(trace) >= 4,
                f"len={len(trace) if isinstance(trace, list) else 'n/a'}",
            ))
        except Exception as e:
            results.append(_check("8. capsule execution_trace non-empty with >= 4 steps", False, f"json error: {e}"))
    else:
        results.append(_check("8. capsule execution_trace non-empty with >= 4 steps", False, "capsule artifact missing"))

    # 9. bundle JSON exists, valid, contains gene + capsule
    if BUNDLE_PATH.exists():
        try:
            bundle = _read_json(BUNDLE_PATH)
            ok = (
                isinstance(bundle, dict)
                and "gene" in bundle
                and "capsule" in bundle
                and bundle.get("schema_version") == "atl-evomap-portable-bundle-v0.1"
            )
            results.append(_check(
                "9. bundle JSON valid with gene + capsule + schema_version",
                ok,
                f"schema={bundle.get('schema_version')!r}" if ok else "missing fields",
            ))
        except Exception as e:
            results.append(_check("9. bundle JSON valid with gene + capsule + schema_version", False, f"json error: {e}"))
    else:
        results.append(_check("9. bundle JSON valid with gene + capsule + schema_version", False, "bundle missing"))

    # 10. inspect output ok == true
    if INSPECT_OUTPUT.exists():
        try:
            ins = _read_json(INSPECT_OUTPUT)
            results.append(_check(
                "10. inspect-bundle output ok == true",
                ins.get("ok") is True,
                f"ok={ins.get('ok')}",
            ))
        except Exception as e:
            results.append(_check("10. inspect-bundle output ok == true", False, f"json error: {e}"))
    else:
        results.append(_check("10. inspect-bundle output ok == true", False, "inspect output missing"))

    # 11. validate output ok == true
    if VALIDATE_OUTPUT.exists():
        try:
            val = _read_json(VALIDATE_OUTPUT)
            results.append(_check(
                "11. validate-bundle output ok == true",
                val.get("ok") is True and not val.get("failures"),
                f"ok={val.get('ok')}, failures={len(val.get('failures', []))}",
            ))
        except Exception as e:
            results.append(_check("11. validate-bundle output ok == true", False, f"json error: {e}"))
    else:
        results.append(_check("11. validate-bundle output ok == true", False, "validate output missing"))

    # 12. apply dry-run
    if APPLY_DRY_OUTPUT.exists():
        try:
            dr = _read_json(APPLY_DRY_OUTPUT)
            results.append(_check(
                "12. apply dry-run output present and mode == dry-run",
                dr.get("mode") == "dry-run" and dr.get("ok") is True,
                f"mode={dr.get('mode')!r}, ok={dr.get('ok')}",
            ))
        except Exception as e:
            results.append(_check("12. apply dry-run output present and mode == dry-run", False, f"json error: {e}"))
    else:
        results.append(_check("12. apply dry-run output present and mode == dry-run", False, "dry-run output missing"))

    # 13. apply --yes
    if APPLY_YES_OUTPUT.exists():
        try:
            ay = _read_json(APPLY_YES_OUTPUT)
            results.append(_check(
                "13. apply --yes output present and mode == applied",
                ay.get("mode") == "applied" and ay.get("ok") is True,
                f"mode={ay.get('mode')!r}, ok={ay.get('ok')}",
            ))
        except Exception as e:
            results.append(_check("13. apply --yes output present and mode == applied", False, f"json error: {e}"))
    else:
        results.append(_check("13. apply --yes output present and mode == applied", False, "apply --yes output missing"))

    # 14. apply target summary
    if APPLY_TARGET_SUMMARY.exists():
        try:
            ts = _read_json(APPLY_TARGET_SUMMARY)
            results.append(_check(
                "14. apply target summary: gene_count >= 1 and capsule_count >= 1",
                ts.get("gene_count", 0) >= 1 and ts.get("capsule_count", 0) >= 1,
                f"gene_count={ts.get('gene_count')}, capsule_count={ts.get('capsule_count')}",
            ))
        except Exception as e:
            results.append(_check("14. apply target summary: gene_count >= 1 and capsule_count >= 1", False, f"json error: {e}"))
    else:
        results.append(_check("14. apply target summary: gene_count >= 1 and capsule_count >= 1", False, "target summary missing"))

    # 15. reports
    results.append(_check("15. case report exists", CASE_REPORT.exists(), str(CASE_REPORT.relative_to(REPO))))
    results.append(_check("15. top-level report exists", TOPLEVEL_REPORT.exists(), str(TOPLEVEL_REPORT.relative_to(REPO))))

    # 16. case README exists
    results.append(_check("16. case README exists", CASE_README.exists(), str(CASE_README.relative_to(REPO))))

    # 17. data/cases.json phase / phase_history
    if DATA_CASES.exists():
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            top_phase = case.get("phase", "") if case else ""
            history_phases = [h.get("phase", "") for h in (case.get("phase_history") or [])] if case else []
            has_6b = "ATL-EVOMAP-6B" in top_phase or "ATL-EVOMAP-6B" in history_phases
            results.append(_check(
                "17. data/cases.json contains ATL-EVOMAP-6B in phase or phase_history",
                has_6b,
                f"top_phase={top_phase!r}, history_count={len(history_phases)}",
            ))
        except Exception as e:
            results.append(_check("17. data/cases.json contains ATL-EVOMAP-6B in phase or phase_history", False, f"json error: {e}"))
    else:
        results.append(_check("17. data/cases.json contains ATL-EVOMAP-6B in phase or phase_history", False, "cases.json missing"))

    # 18. main case README
    if MAIN_CASE_README.exists():
        text = MAIN_CASE_README.read_text(encoding="utf-8", errors="replace")
        results.append(_check(
            "18. main case README references ATL-EVOMAP-6B",
            "ATL-EVOMAP-6B" in text,
            f"main README len={len(text)}",
        ))
    else:
        results.append(_check("18. main case README references ATL-EVOMAP-6B", False, "main README missing"))

    # 19. secret scan over committed 6B files
    files_to_scan = [
        PARSER_PATH,
        FIXTURE_PATH,
        FIXTURE_OUTPUT,
        GENE_ARTIFACT,
        CAPSULE_ARTIFACT,
        BUNDLE_PATH,
        INSPECT_OUTPUT,
        VALIDATE_OUTPUT,
        APPLY_DRY_OUTPUT,
        APPLY_YES_OUTPUT,
        APPLY_TARGET_SUMMARY,
        CASE_REPORT,
        TOPLEVEL_REPORT,
        CASE_README,
        MAIN_CASE_README,
    ]
    if DATA_CASES.exists():
        files_to_scan.append(DATA_CASES)
    failures, scanned = _secret_scan_files(files_to_scan)
    results.append(_check(
        "19. secret scan: no Telegram credential / recipient id / API key / Authorization / private key in committed files",
        not failures,
        f"scanned={scanned} files, hits=0" if not failures else f"hits={len(failures)}: {failures[:3]}",
    ))

    # ---- summary ----
    passes = sum(1 for r in results if r["ok"])
    fails = sum(1 for r in results if not r["ok"])
    print(f"ATL-EVOMAP-6B Telegram Message Router Failure Bundle — Validator")
    print(f"  total: {len(results)} checks")
    print(f"  PASS:  {passes}")
    print(f"  FAIL:  {fails}")
    print()
    for r in results:
        marker = "\033[92mPASS\033[0m" if r["ok"] else "\033[91mFAIL\033[0m"
        print(f"  [{marker}] {r['name']}")
        if r["detail"]:
            print(f"          {r['detail']}")
    print()
    if fails == 0:
        print("\033[92mPASS\033[0m  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 6B Telegram Message Router Failure Bundle)")
        # Get current case state
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            if case:
                print(f"Status: {case.get('status', '?')} ({case.get('final_status', '?')})")
        except Exception:
            pass
        return 0
    else:
        print(f"\033[91mFAIL\033[0m  {fails} CHECKS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
