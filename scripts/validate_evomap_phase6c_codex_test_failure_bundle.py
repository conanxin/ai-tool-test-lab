#!/usr/bin/env python3
"""
validate_evomap_phase6c_codex_test_failure_bundle.py — Phase 6C Validator (23 checks)

Forwards-compatible: accepts ATL-EVOMAP-5/6A/6B/7A/7B/6C entries in
phase_history so this validator stays green as the case progresses.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, subprocess)
- Runs in current working directory (the ai-tool-test-lab repo root)
- Does NOT contact Hub, does NOT publish, does NOT consume credits
- Does NOT execute evolver --approve or evolver solidify
- Does NOT commit runtime .evolver/ or memory/ originals
- Pure file-level + JSON-level checks; no network calls; no shell exec for
  curl/wget/HTTP

Checks (23):
 1.  scripts/codex_test_failure_loop_fixture.py exists (stdlib only, --input only)
 2.  fixture file exists
 3.  fixture output JSON exists and ok=true
 4.  fixture output: tests_failed == true
 5.  fixture output: repeated_failure_count == 3
 6.  fixture output: failing_assertion_detected == true
 7.  fixture output: regression_introduced == true
 8.  fixture output: fix_one_break_another == true
 9.  fixture output: final_green_test_missing == true
10.  3 parser self-test outputs exist (openai-key, github-pat, env-path); all ok=false
11.  3 selftest artifacts do not contain full unsafe raw strings
12.  gene artifact exists and contains 'gene_distilled_codex-test-failure-loop'
13.  capsule artifact exists and contains 'capsule_codex_test_failure_loop_phase6c'
14.  capsule.execution_trace is non-empty list with >= 4 steps
15.  bundle/codex-test-failure-loop.bundle.json exists and JSON is valid
16.  inspect-codex-bundle-output.json exists and ok=true
17.  validate-codex-bundle-output.json exists and ok=true
18.  apply-codex-bundle-dry-run-output.json exists and ok=true
19.  apply-codex-bundle-yes-output.json exists and ok=true
20.  apply-codex-target-summary.json: gene_count >= 1, capsule_count >= 1
21.  apply-codex-target-summary.json signals contain test_failure, repeated_test_failure, failing_assertion, fix_one_break_another, final_green_test_missing
22.  evolver-run-codex-target-output.txt contains 'No hub match' or 'no_hub_url' (combined smoke no-Hub confirmation)
23.  data/cases.json + main case README + secret scan + git status + 5 prior validators
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root (cwd). All paths are relative to this.
REPO = Path.cwd()

CASE = REPO / "cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle"
ART = CASE / "artifacts"
PARSER = REPO / "scripts" / "codex_test_failure_loop_fixture.py"
FIXTURE = CASE / "fixtures" / "codex-test-failure-loop-sample.txt"
GENE_ART = ART / "gene-codex-test-failure-loop.json"
CAP_ART = ART / "capsule-codex-test-failure-loop.json"
BUNDLE = CASE / "bundle" / "codex-test-failure-loop.bundle.json"
CASE_REPORT = CASE / "ATL_EVOMAP_6C_CODEX_TEST_FAILURE_BUNDLE_REPORT.md"
TOPLEVEL_REPORT = REPO / "reports" / "ATL_EVOMAP_6C_CODEX_TEST_FAILURE_BUNDLE_REPORT.md"
CASE_README = CASE / "README.md"
MAIN_CASE_README = REPO / "cases/evomap-evolver-openclaw-v0/README.md"
DATA_CASES = REPO / "data/cases.json"

# Secret patterns — used for the secret scan
SECRET_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)authorization\s*[:=]\s*[A-Za-z0-9_\-\.=]{16,}"),
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b\d{12,}\b"),
]

# Files that legitimately document / describe the secret patterns
# (e.g. parser source describing the unsafe-string detection rules) or
# contain evolver run / review output that may legitimately have 13-digit
# Unix-ms timestamps that match the long-digit heuristic.
ALLOW_SECRET_PATTERNS_IN_FILES = {
    "evomap_apply_bundle.py",
    "validate_evomap_phase7a_domain_signal_injection.py",
    "validate_evomap_phase7b_cross_bundle_regression.py",
    "validate_evomap_phase7b_cross_bundle_regression.py",
    "validate_evomap_phase6c_codex_test_failure_bundle.py",
    "validate_evomap_phase6b_telegram_router_bundle.py",
    "validate_evomap_phase6a_hermes_systemd_bundle.py",
    "validate_evomap_phase5_local_evolution_kit.py",
    "codex_test_failure_loop_fixture.py",
    "evolver-run-codex-target-output.txt",
    "evolver-review-codex-target-output.txt",
    "evolver-run-cross-bundle-output.txt",
    "evolver-review-cross-bundle-output.txt",
    "evolver-run-probe-openclaw-output.txt",
    "evolver-review-probe-openclaw-output.txt",
    "evolver-run-probe-hermes-output.txt",
    "evolver-review-probe-hermes-output.txt",
    "evolver-run-probe-telegram-output.txt",
    "evolver-review-probe-telegram-output.txt",
    "evomap_cross_bundle_analyze.py",
}


# -------- helpers --------

def _check(name, ok, detail=""):
    return {"name": name, "ok": bool(ok), "detail": str(detail)}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _secret_scan_files(paths):
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
            for m in pat.finditer(text):
                excerpt = m.group()
                if p.name in ALLOW_SECRET_PATTERNS_IN_FILES:
                    continue
                failures.append((str(p), pat.pattern, excerpt[:50]))
    return failures, scanned


def _read_apply_output(path: Path):
    d = _read_json(path)
    if d.get("mode") == "applied":
        return {
            "ok": d.get("ok"),
            "mode": d.get("signal_injection_mode"),
            "memory_signals": d.get("plan_summary", {}).get("memory_graph_signals_added"),
            "new_gene_count": d.get("plan_summary", {}).get("new_gene_count"),
            "new_capsule_count": d.get("plan_summary", {}).get("new_capsule_count"),
        }
    if d.get("mode") == "dry-run":
        plan = d.get("plan", {})
        return {
            "ok": d.get("ok"),
            "mode": plan.get("signal_injection_mode"),
            "memory_signals": plan.get("summary", {}).get("memory_graph_signals_added"),
            "new_gene_count": plan.get("summary", {}).get("new_gene_count"),
            "new_capsule_count": plan.get("summary", {}).get("new_capsule_count"),
        }
    return {"ok": False, "mode": "unknown"}


def main():
    parser = argparse.ArgumentParser(
        description="Validator for ATL-EVOMAP-6C Codex Test Failure Loop Bundle."
    )
    parser.add_argument("--strict", action="store_true", help="(no-op) this validator is strict by default")
    args = parser.parse_args()

    results = []

    # 1. parser exists, stdlib only, --input only
    if PARSER.exists():
        text = PARSER.read_text(encoding="utf-8", errors="replace")
        has_input = "--input" in text
        has_path_refusal = "_refuse_input_path" in text
        has_content_refusal = "_scan_text_safety" in text
        # stdlib only
        import_lines = [
            ln.strip() for ln in text.splitlines()
            if ln.strip().startswith("import ") or ln.strip().startswith("from ")
        ]
        non_stdlib = [
            ln for ln in import_lines
            if not re.match(r"^(import|from)\s+(argparse|json|re|sys|pathlib|os|typing|dataclasses|collections|functools|itertools|io|hashlib|hmac|secrets|uuid|datetime|__future__)(\s|\.|$| import)", ln)
            and "__future__" not in ln
        ]
        ok = has_input and has_path_refusal and has_content_refusal and not non_stdlib
        results.append(_check(
            "1. parser exists, --input only, stdlib only, has path refusal + content refusal",
            ok,
            f"input={has_input} path_refusal={has_path_refusal} content_refusal={has_content_refusal} non_stdlib_imports={non_stdlib}",
        ))
    else:
        results.append(_check("1. parser exists, --input only, stdlib only, has path refusal + content refusal", False, "missing"))

    # 2. fixture file exists
    results.append(_check("2. fixture file exists", FIXTURE.exists(), str(FIXTURE.relative_to(REPO))))

    # 3. fixture output JSON exists and ok=true
    p = ART / "codex-test-failure-fixture-output.json"
    if p.exists():
        d = _read_json(p)
        results.append(_check(
            "3. fixture output JSON exists and ok=true",
            d.get("ok") is True,
            f"ok={d.get('ok')}",
        ))
    else:
        results.append(_check("3. fixture output JSON exists and ok=true", False, "missing"))

    # 4-9. fixture output spec fields
    p = ART / "codex-test-failure-fixture-output.json"
    if p.exists():
        d = _read_json(p)
        results.append(_check(
            "4. fixture output: tests_failed == true",
            d.get("tests_failed") is True,
            f"tests_failed={d.get('tests_failed')}",
        ))
        results.append(_check(
            "5. fixture output: repeated_failure_count == 3",
            d.get("repeated_failure_count") == 3,
            f"repeated_failure_count={d.get('repeated_failure_count')}",
        ))
        results.append(_check(
            "6. fixture output: failing_assertion_detected == true",
            d.get("failing_assertion_detected") is True,
            f"failing_assertion_detected={d.get('failing_assertion_detected')}",
        ))
        results.append(_check(
            "7. fixture output: regression_introduced == true",
            d.get("regression_introduced") is True,
            f"regression_introduced={d.get('regression_introduced')}",
        ))
        results.append(_check(
            "8. fixture output: fix_one_break_another == true",
            d.get("fix_one_break_another") is True,
            f"fix_one_break_another={d.get('fix_one_break_another')}",
        ))
        results.append(_check(
            "9. fixture output: final_green_test_missing == true",
            d.get("final_green_test_missing") is True,
            f"final_green_test_missing={d.get('final_green_test_missing')}",
        ))
    else:
        for i in range(4, 10):
            results.append(_check(f"{i}. fixture output spec field", False, "missing"))

    # 10. 3 parser self-test outputs exist and all ok=false
    selftests = [
        ("openai-key", ART / "parser-selftest-openai-key-output.json"),
        ("github-pat", ART / "parser-selftest-github-pat-output.json"),
        ("env-path",  ART / "parser-selftest-env-path-output.json"),
    ]
    selftest_ok = True
    selftest_detail = []
    for name, p in selftests:
        if not p.exists():
            selftest_ok = False
            selftest_detail.append(f"{name}: missing")
            continue
        d = _read_json(p)
        if d.get("ok") is not False:
            selftest_ok = False
            selftest_detail.append(f"{name}: ok={d.get('ok')!r}")
        else:
            selftest_detail.append(f"{name}: ok=false, error={d.get('error')!r}")
    results.append(_check(
        "10. 3 parser self-test outputs exist; all ok=false",
        selftest_ok,
        "; ".join(selftest_detail),
    ))

    # 11. selftest artifacts do not contain full unsafe raw strings
    UNSAFE_SAFE_INDICATORS = [
        "sk-X",
        "ghp_Y",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # 48 X's
        "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",              # 36 Y's
    ]
    unsafe_hits = []
    for name, p in selftests:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for ind in UNSAFE_SAFE_INDICATORS:
            if ind in text:
                unsafe_hits.append(f"{name}: {ind!r}")
    results.append(_check(
        "11. selftest artifacts do not contain full unsafe raw strings",
        not unsafe_hits,
        f"0 hits across 3 selftest artifacts" if not unsafe_hits else f"hits={unsafe_hits}",
    ))

    # 12. gene artifact exists and contains gene_distilled_codex-test-failure-loop
    if GENE_ART.exists():
        d = _read_json(GENE_ART)
        results.append(_check(
            "12. gene artifact exists and contains 'gene_distilled_codex-test-failure-loop'",
            d.get("id") == "gene_distilled_codex-test-failure-loop" and d.get("type") == "Gene",
            f"id={d.get('id')}, type={d.get('type')}",
        ))
    else:
        results.append(_check("12. gene artifact exists and contains 'gene_distilled_codex-test-failure-loop'", False, "missing"))

    # 13. capsule artifact exists and contains capsule_codex_test_failure_loop_phase6c
    if CAP_ART.exists():
        d = _read_json(CAP_ART)
        results.append(_check(
            "13. capsule artifact exists and contains 'capsule_codex_test_failure_loop_phase6c'",
            d.get("id") == "capsule_codex_test_failure_loop_phase6c" and d.get("type") == "Capsule",
            f"id={d.get('id')}, type={d.get('type')}",
        ))
    else:
        results.append(_check("13. capsule artifact exists and contains 'capsule_codex_test_failure_loop_phase6c'", False, "missing"))

    # 14. capsule.execution_trace is non-empty list with >= 4 steps
    if CAP_ART.exists():
        d = _read_json(CAP_ART)
        trace = d.get("execution_trace", [])
        results.append(_check(
            "14. capsule.execution_trace is non-empty list with >= 4 steps",
            isinstance(trace, list) and len(trace) >= 4,
            f"type={type(trace).__name__}, len={len(trace) if isinstance(trace, list) else 'N/A'}",
        ))
    else:
        results.append(_check("14. capsule.execution_trace is non-empty list with >= 4 steps", False, "missing"))

    # 15. bundle JSON is valid
    if BUNDLE.exists():
        try:
            d = _read_json(BUNDLE)
            results.append(_check(
                "15. bundle/codex-test-failure-loop.bundle.json exists and JSON is valid",
                d.get("schema_version") == "atl-evomap-portable-bundle-v0.1",
                f"schema_version={d.get('schema_version')}",
            ))
        except Exception as e:
            results.append(_check("15. bundle/codex-test-failure-loop.bundle.json exists and JSON is valid", False, f"json error: {e}"))
    else:
        results.append(_check("15. bundle/codex-test-failure-loop.bundle.json exists and JSON is valid", False, "missing"))

    # 16. inspect-codex-bundle-output.json exists and ok=true
    p = ART / "inspect-codex-bundle-output.json"
    if p.exists():
        d = _read_json(p)
        results.append(_check(
            "16. inspect-codex-bundle-output.json exists and ok=true",
            d.get("ok") is True,
            f"ok={d.get('ok')}",
        ))
    else:
        results.append(_check("16. inspect-codex-bundle-output.json exists and ok=true", False, "missing"))

    # 17. validate-codex-bundle-output.json exists and ok=true
    p = ART / "validate-codex-bundle-output.json"
    if p.exists():
        d = _read_json(p)
        results.append(_check(
            "17. validate-codex-bundle-output.json exists and ok=true",
            d.get("ok") is True,
            f"ok={d.get('ok')}, failures={d.get('failures', [])[:3]}",
        ))
    else:
        results.append(_check("17. validate-codex-bundle-output.json exists and ok=true", False, "missing"))

    # 18. apply-codex-bundle-dry-run-output.json exists and ok=true
    p = ART / "apply-codex-bundle-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "18. apply-codex-bundle-dry-run-output.json exists and ok=true & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("18. apply-codex-bundle-dry-run-output.json exists and ok=true & mode=generic_plus_domain_from_bundle", False, "missing"))

    # 19. apply-codex-bundle-yes-output.json exists and ok=true & gene=1 & capsule=1 & 27 memory signals
    p = ART / "apply-codex-bundle-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "19. apply-codex-bundle-yes-output.json exists and ok=true & mode=generic_plus_domain_from_bundle & gene=1 & capsule=1 & 27 memory signals",
            d.get("ok") is True
            and d.get("mode") == "generic_plus_domain_from_bundle"
            and d.get("new_gene_count") == 1
            and d.get("new_capsule_count") == 1
            and d.get("memory_signals") == 27,
            f"ok={d.get('ok')}, mode={d.get('mode')}, gene={d.get('new_gene_count')}, cap={d.get('new_capsule_count')}, mem={d.get('memory_signals')}",
        ))
    else:
        results.append(_check("19. apply-codex-bundle-yes-output.json exists and ok=true & mode=generic_plus_domain_from_bundle & gene=1 & capsule=1 & 27 memory signals", False, "missing"))

    # 20. apply-codex-target-summary.json: gene_count >= 1, capsule_count >= 1
    p = ART / "apply-codex-target-summary.json"
    if p.exists():
        d = _read_json(p)
        results.append(_check(
            "20. apply-codex-target-summary.json: gene_count >= 1, capsule_count >= 1",
            d.get("gene_count", 0) >= 1 and d.get("capsule_count", 0) >= 1,
            f"gene_count={d.get('gene_count')}, capsule_count={d.get('capsule_count')}",
        ))
    else:
        results.append(_check("20. apply-codex-target-summary.json: gene_count >= 1, capsule_count >= 1", False, "missing"))

    # 21. apply-codex-target-summary.json signals contain test_failure / repeated_test_failure / failing_assertion / fix_one_break_another / final_green_test_missing
    p = ART / "apply-codex-target-summary.json"
    if p.exists():
        d = _read_json(p)
        signals = d.get("signals", [])
        required = ["test_failure", "repeated_test_failure", "failing_assertion", "fix_one_break_another", "final_green_test_missing"]
        missing = [s for s in required if s not in signals]
        results.append(_check(
            "21. apply-codex-target-summary.json signals contain test_failure, repeated_test_failure, failing_assertion, fix_one_break_another, final_green_test_missing",
            not missing,
            f"missing={missing}" if missing else f"all 5 required signals present in {len(signals)} distinct signals",
        ))
    else:
        results.append(_check("21. apply-codex-target-summary.json signals contain test_failure, repeated_test_failure, failing_assertion, fix_one_break_another, final_green_test_missing", False, "missing"))

    # 22. evolver-run-codex-target-output.txt contains 'No hub match' or 'no_hub_url'
    p = ART / "evolver-run-codex-target-output.txt"
    if p.exists():
        text = p.read_text(encoding="utf-8", errors="replace")
        has_hub_match = "No hub match" in text or "no_hub_url" in text
        results.append(_check(
            "22. evolver-run-codex-target-output.txt contains 'No hub match' or 'no_hub_url' (combined smoke no-Hub confirmation)",
            has_hub_match,
            "found in evolver run output" if has_hub_match else "missing",
        ))
    else:
        results.append(_check("22. evolver-run-codex-target-output.txt contains 'No hub match' or 'no_hub_url' (combined smoke no-Hub confirmation)", False, "missing"))

    # 23. data/cases.json + main case README + secret scan + git status + 5 prior validators
    # 23a. data/cases.json
    has_6c = False
    if DATA_CASES.exists():
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            top_phase = case.get("phase", "") if case else ""
            history_phases = [h.get("phase", "") for h in (case.get("phase_history") or [])] if case else []
            has_6c = "ATL-EVOMAP-6C" in top_phase or "ATL-EVOMAP-6C" in history_phases
        except Exception:
            has_6c = False
    # 23b. main case README
    has_6c_readme = False
    if MAIN_CASE_README.exists():
        text = MAIN_CASE_README.read_text(encoding="utf-8", errors="replace")
        has_6c_readme = "ATL-EVOMAP-6C" in text
    # 23c. secret scan
    files_to_scan = [
        PARSER, FIXTURE, GENE_ART, CAP_ART, BUNDLE, CASE_REPORT, TOPLEVEL_REPORT, CASE_README, MAIN_CASE_README,
    ]
    if ART.exists():
        for f in sorted(ART.glob("*.json")):
            files_to_scan.append(f)
        for f in sorted(ART.glob("*.txt")):
            files_to_scan.append(f)
    if DATA_CASES.exists():
        files_to_scan.append(DATA_CASES)
    sec_fails, sec_scanned = _secret_scan_files(files_to_scan)
    # 23d. git status: no root .evolver/ or memory/ tracked
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=str(REPO), capture_output=True, text=True, check=True
        ).stdout
        tracked = [
            l for l in out.splitlines()
            if l == ".evolver" or l.startswith(".evolver/") or l == "memory" or l.startswith("memory/")
        ]
        git_clean = not tracked
    except Exception:
        git_clean = False
    # 23e. 5 prior validators ALL CHECKS PASSED
    validators = [
        ("Phase 5", REPO / "scripts" / "validate_evomap_phase5_local_evolution_kit.py"),
        ("Phase 6A", REPO / "scripts" / "validate_evomap_phase6a_hermes_systemd_bundle.py"),
        ("Phase 6B", REPO / "scripts" / "validate_evomap_phase6b_telegram_router_bundle.py"),
        ("Phase 7A", REPO / "scripts" / "validate_evomap_phase7a_domain_signal_injection.py"),
        ("Phase 7B", REPO / "scripts" / "validate_evomap_phase7b_cross_bundle_regression.py"),
    ]
    val_failed = []
    for name, vp in validators:
        if not vp.exists():
            val_failed.append(f"{name}: missing")
            continue
        try:
            r = subprocess.run(["python3", str(vp)], cwd=str(REPO), capture_output=True, text=True, timeout=60)
            if "ALL CHECKS PASSED" not in r.stdout:
                val_failed.append(f"{name}: rc={r.returncode}")
        except Exception as e:
            val_failed.append(f"{name}: {e}")
    all_ok = has_6c and has_6c_readme and not sec_fails and git_clean and not val_failed
    detail = (
        f"data/cases.json_6c={has_6c}, "
        f"main_README_6c={has_6c_readme}, "
        f"secret_scan={sec_scanned} files, {len(sec_fails)} hits, "
        f"git_root_evolver_or_memory_tracked={not git_clean}, "
        f"5_prior_validators={'PASS' if not val_failed else 'FAILED: ' + str(val_failed)}"
    )
    results.append(_check(
        "23. data/cases.json + main case README + secret scan + git status + 5 prior validators (composite)",
        all_ok,
        detail,
    ))

    # ---- summary ----
    passes = sum(1 for r in results if r["ok"])
    fails = sum(1 for r in results if not r["ok"])
    print("ATL-EVOMAP-6C Codex Test Failure Loop Bundle — Validator")
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
        print("Case: evomap-evolver-openclaw-v0 (Phase 6C Codex Test Failure Loop Bundle)")
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
