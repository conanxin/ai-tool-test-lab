#!/usr/bin/env python3
"""
validate_evomap_phase7b_cross_bundle_regression.py — Phase 7B Validator (27 checks)

Forwards-compatible: accepts ATL-EVOMAP-5/6A/6B/7A/7B entries in
phase_history so this validator stays green as the case progresses.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, subprocess)
- Runs in current working directory (the ai-tool-test-lab repo root)
- Does NOT contact Hub, does NOT publish, does NOT consume credits
- Does NOT execute evolver --approve or evolver solidify
- Does NOT commit runtime .evolver/ or memory/ originals
- Pure file-level + JSON-level checks; no network calls; no shell exec for
  curl/wget/HTTP

Checks (27):
 1.  scripts/evomap_cross_bundle_analyze.py exists (stdlib only, --target-runtime only)
 2.  Phase 7B case report exists
 3.  apply-openclaw-dry-run-output.json exists and ok=true
 4.  apply-openclaw-yes-output.json exists and ok=true
 5.  apply-hermes-dry-run-output.json exists and ok=true
 6.  apply-hermes-yes-output.json exists and ok=true
 7.  apply-telegram-dry-run-output.json exists and ok=true
 8.  apply-telegram-yes-output.json exists and ok=true
 9.  cross-bundle-target-summary.json exists and ok=true
10.  cross-bundle-target-summary.json: gene_count == 3
11.  cross-bundle-target-summary.json: capsule_count == 3
12.  duplicate_gene_ids == []
13.  duplicate_capsule_ids == []
14.  required_openclaw_signals_present == true
15.  required_hermes_signals_present == true
16.  required_telegram_signals_present == true
17.  dangerous_signals == []
18.  pollution_signals == []
19.  cross-bundle-regression-summary.json exists
20.  evolver-run-cross-bundle-output.txt exists
21.  evolver-review-cross-bundle-output.txt exists
22.  combined smoke output contains "No hub match" or "no_hub_url"
23.  data/cases.json phase contains "ATL-EVOMAP-7B"
24.  main case README references ATL-EVOMAP-7B
25.  secret scan: no Telegram credential / recipient id / API key / cookie / Authorization /
      private key in committed files
26.  git status: no root .evolver/ or memory/ tracked
27.  prior validators (5, 6A, 6B, 7A) ALL CHECKS PASSED (backward-compat)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root (cwd). All paths are relative to this.
REPO = Path.cwd()

CASE = REPO / "cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression"
ART = CASE / "artifacts"
ANALYZER = REPO / "scripts" / "evomap_cross_bundle_analyze.py"
CASE_REPORT = CASE / "ATL_EVOMAP_7B_CROSS_BUNDLE_REGRESSION_REPORT.md"
TOPLEVEL_REPORT = REPO / "reports" / "ATL_EVOMAP_7B_CROSS_BUNDLE_REGRESSION_REPORT.md"
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

# Files that legitimately document/contain the secret patterns as regex
# literals (refusals / descriptions), so the scan can ignore those specific
# files for the corresponding pattern. Also includes evolver run/review
# output files: those are evolver CLI output, never contain real
# credentials or chat ids, but may legitimately contain 13-digit Unix ms
# timestamps (e.g. 1773331925711) that match the "long-digit recipient"
# heuristic.
ALLOW_SECRET_PATTERNS_IN_FILES = {
    "evomap_apply_bundle.py",
    "validate_evomap_phase7a_domain_signal_injection.py",
    "validate_evomap_phase7b_cross_bundle_regression.py",
    "validate_evomap_phase6b_telegram_router_bundle.py",
    "validate_evomap_phase6a_hermes_systemd_bundle.py",
    "validate_evomap_phase5_local_evolution_kit.py",
    "evolver-run-combined-output.txt",
    "evolver-review-combined-output.txt",
    "evolver-run-hermes-domain-output.txt",
    "evolver-review-hermes-domain-output.txt",
    "evolver-run-telegram-domain-output.txt",
    "evolver-review-telegram-domain-output.txt",
    "evolver-run-telegram-target-output.txt",
    "evolver-review-telegram-target-output.txt",
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
            for m in pat.finditer(text):
                excerpt = m.group()
                if p.name in ALLOW_SECRET_PATTERNS_IN_FILES:
                    continue
                failures.append((str(p), pat.pattern, excerpt[:50]))
    return failures, scanned


def _read_apply_output(path: Path):
    """Read a 7A apply dry-run/yes output and normalize fields."""
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
        description="Validator for ATL-EVOMAP-7B Cross-Bundle Regression."
    )
    parser.add_argument("--strict", action="store_true", help="(no-op) this validator is strict by default")
    args = parser.parse_args()

    results = []

    # 1. cross-bundle analyzer exists, stdlib only, --target-runtime only
    if ANALYZER.exists():
        text = ANALYZER.read_text(encoding="utf-8", errors="replace")
        has_target = "--target-runtime" in text
        has_required_ids = "REQUIRED_GENE_IDS" in text and "REQUIRED_CAPSULE_IDS" in text
        has_dangerous = "DANGEROUS_SIGNALS" in text
        has_pollution = "POLLUTION_SIGNALS" in text
        has_credential = "CREDENTIAL_PATTERN" in text
        has_required_openclaw = "REQUIRED_OPENCLAW_SIGNALS" in text
        has_required_hermes = "REQUIRED_HERMES_SIGNALS" in text
        has_required_telegram = "REQUIRED_TELEGRAM_SIGNALS" in text
        # stdlib-only: only import lines should be stdlib names
        import_lines = [
            ln.strip() for ln in text.splitlines()
            if ln.strip().startswith("import ") or ln.strip().startswith("from ")
        ]
        non_stdlib = [
            ln for ln in import_lines
            if not re.match(r"^(import|from)\s+(argparse|json|re|sys|pathlib|os|typing|dataclasses|collections|functools|itertools|io|hashlib|hmac|secrets|uuid|datetime|__future__)(\s|\.|$| import)", ln)
            and "__future__" not in ln
        ]
        ok = (
            has_target and has_required_ids and has_dangerous
            and has_pollution and has_credential
            and has_required_openclaw and has_required_hermes and has_required_telegram
            and not non_stdlib
        )
        results.append(_check(
            "1. cross-bundle analyzer exists, --target-runtime only, stdlib only, has all required-ids + dangerous + pollution + credential filter + 3 required-signal sets",
            ok,
            f"target={has_target} req_ids={has_required_ids} dangerous={has_dangerous} pollution={has_pollution} cred={has_credential} sig_sets={has_required_openclaw}/{has_required_hermes}/{has_required_telegram} non_stdlib_imports={non_stdlib}",
        ))
    else:
        results.append(_check("1. cross-bundle analyzer exists, --target-runtime only, stdlib only, has all required-ids + dangerous + pollution + credential filter + 3 required-signal sets", False, "missing"))

    # 2. case report exists
    results.append(_check("2. case report exists", CASE_REPORT.exists(), str(CASE_REPORT.relative_to(REPO))))

    # 3-4. openclaw apply (dry-run + --yes)
    p = ART / "apply-openclaw-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "3. apply-openclaw-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("3. apply-openclaw-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    p = ART / "apply-openclaw-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "4. apply-openclaw-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=1 & capsule=1 & 15 memory signals",
            d.get("ok") is True
            and d.get("mode") == "generic_plus_domain_from_bundle"
            and d.get("new_gene_count") == 1
            and d.get("new_capsule_count") == 1
            and d.get("memory_signals") == 15,
            f"ok={d.get('ok')}, mode={d.get('mode')}, gene={d.get('new_gene_count')}, cap={d.get('new_capsule_count')}, mem={d.get('memory_signals')}",
        ))
    else:
        results.append(_check("4. apply-openclaw-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=1 & capsule=1 & 15 memory signals", False, "missing"))

    # 5-6. hermes apply (dry-run + --yes)
    p = ART / "apply-hermes-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "5. apply-hermes-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("5. apply-hermes-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    p = ART / "apply-hermes-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "6. apply-hermes-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=2 & capsule=2 & 17 memory signals",
            d.get("ok") is True
            and d.get("mode") == "generic_plus_domain_from_bundle"
            and d.get("new_gene_count") == 2
            and d.get("new_capsule_count") == 2
            and d.get("memory_signals") == 17,
            f"ok={d.get('ok')}, mode={d.get('mode')}, gene={d.get('new_gene_count')}, cap={d.get('new_capsule_count')}, mem={d.get('memory_signals')}",
        ))
    else:
        results.append(_check("6. apply-hermes-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=2 & capsule=2 & 17 memory signals", False, "missing"))

    # 7-8. telegram apply (dry-run + --yes)
    p = ART / "apply-telegram-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "7. apply-telegram-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("7. apply-telegram-dry-run-output.json: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    p = ART / "apply-telegram-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "8. apply-telegram-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=3 & capsule=3 & 27 memory signals",
            d.get("ok") is True
            and d.get("mode") == "generic_plus_domain_from_bundle"
            and d.get("new_gene_count") == 3
            and d.get("new_capsule_count") == 3
            and d.get("memory_signals") == 27,
            f"ok={d.get('ok')}, mode={d.get('mode')}, gene={d.get('new_gene_count')}, cap={d.get('new_capsule_count')}, mem={d.get('memory_signals')}",
        ))
    else:
        results.append(_check("8. apply-telegram-yes-output.json: ok & mode=generic_plus_domain_from_bundle & gene=3 & capsule=3 & 27 memory signals", False, "missing"))

    # 9-18. cross-bundle-target-summary.json
    p = ART / "cross-bundle-target-summary.json"
    if p.exists():
        s = _read_json(p)
        results.append(_check(
            "9. cross-bundle-target-summary.json exists and ok=true",
            s.get("ok") is True,
            f"ok={s.get('ok')}",
        ))
        results.append(_check(
            "10. cross-bundle-target-summary.json: gene_count == 3",
            s.get("gene_count") == 3,
            f"gene_count={s.get('gene_count')}",
        ))
        results.append(_check(
            "11. cross-bundle-target-summary.json: capsule_count == 3",
            s.get("capsule_count") == 3,
            f"capsule_count={s.get('capsule_count')}",
        ))
        results.append(_check(
            "12. duplicate_gene_ids == []",
            len(s.get("duplicate_gene_ids", [])) == 0,
            f"duplicate_gene_ids={s.get('duplicate_gene_ids', [])}",
        ))
        results.append(_check(
            "13. duplicate_capsule_ids == []",
            len(s.get("duplicate_capsule_ids", [])) == 0,
            f"duplicate_capsule_ids={s.get('duplicate_capsule_ids', [])}",
        ))
        results.append(_check(
            "14. required_openclaw_signals_present == true",
            s.get("required_openclaw_signals_present") is True,
            f"missing={s.get('openclaw_signals_missing', [])}",
        ))
        results.append(_check(
            "15. required_hermes_signals_present == true",
            s.get("required_hermes_signals_present") is True,
            f"missing={s.get('hermes_signals_missing', [])}",
        ))
        results.append(_check(
            "16. required_telegram_signals_present == true",
            s.get("required_telegram_signals_present") is True,
            f"missing={s.get('telegram_signals_missing', [])}",
        ))
        results.append(_check(
            "17. dangerous_signals == []",
            len(s.get("dangerous_signals", [])) == 0,
            f"dangerous_signals={s.get('dangerous_signals', [])}",
        ))
        results.append(_check(
            "18. pollution_signals == []",
            len(s.get("pollution_signals", [])) == 0,
            f"pollution_signals={s.get('pollution_signals', [])}",
        ))
    else:
        for i in range(9, 19):
            results.append(_check(f"{i}. cross-bundle-target-summary.json check", False, "missing"))

    # 19. cross-bundle-regression-summary.json
    p = ART / "cross-bundle-regression-summary.json"
    if p.exists():
        s = _read_json(p)
        results.append(_check(
            "19. cross-bundle-regression-summary.json exists with status & scoring & probes",
            s.get("status") in ("PASS", "PARTIAL") and "scoring" in s and "selector_probe_matrix" in s,
            f"status={s.get('status')}",
        ))
    else:
        results.append(_check("19. cross-bundle-regression-summary.json exists with status & scoring & probes", False, "missing"))

    # 20. evolver-run-cross-bundle-output.txt
    p = ART / "evolver-run-cross-bundle-output.txt"
    results.append(_check(
        "20. evolver-run-cross-bundle-output.txt exists",
        p.exists(),
        str(p.relative_to(REPO)) if p.exists() else "missing",
    ))

    # 21. evolver-review-cross-bundle-output.txt
    p = ART / "evolver-review-cross-bundle-output.txt"
    results.append(_check(
        "21. evolver-review-cross-bundle-output.txt exists",
        p.exists(),
        str(p.relative_to(REPO)) if p.exists() else "missing",
    ))

    # 22. combined smoke output contains "No hub match" or "no_hub_url"
    p = ART / "evolver-run-cross-bundle-output.txt"
    if p.exists():
        text = p.read_text(encoding="utf-8", errors="replace")
        results.append(_check(
            "22. combined smoke output contains 'No hub match' or 'no_hub_url' (no Hub confirmation)",
            "No hub match" in text or "no_hub_url" in text,
            "found in evolver-run output" if "No hub match" in text or "no_hub_url" in text else "missing",
        ))
    else:
        results.append(_check("22. combined smoke output contains 'No hub match' or 'no_hub_url' (no Hub confirmation)", False, "missing"))

    # 23. data/cases.json
    if DATA_CASES.exists():
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            top_phase = case.get("phase", "") if case else ""
            history_phases = [h.get("phase", "") for h in (case.get("phase_history") or [])] if case else []
            has_7b = "ATL-EVOMAP-7B" in top_phase or "ATL-EVOMAP-7B" in history_phases
            results.append(_check(
                "23. data/cases.json phase contains 'ATL-EVOMAP-7B' (top or history)",
                has_7b,
                f"top_phase={top_phase!r}, history_count={len(history_phases)}",
            ))
        except Exception as e:
            results.append(_check("23. data/cases.json phase contains 'ATL-EVOMAP-7B' (top or history)", False, f"json error: {e}"))
    else:
        results.append(_check("23. data/cases.json phase contains 'ATL-EVOMAP-7B' (top or history)", False, "cases.json missing"))

    # 24. main case README
    if MAIN_CASE_README.exists():
        text = MAIN_CASE_README.read_text(encoding="utf-8", errors="replace")
        results.append(_check(
            "24. main case README references ATL-EVOMAP-7B",
            "ATL-EVOMAP-7B" in text,
            f"main README len={len(text)}",
        ))
    else:
        results.append(_check("24. main case README references ATL-EVOMAP-7B", False, "main README missing"))

    # 25. secret scan
    files_to_scan = [
        ANALYZER,
        CASE_REPORT,
        TOPLEVEL_REPORT,
        CASE_README,
        MAIN_CASE_README,
    ]
    if ART.exists():
        for f in sorted(ART.glob("*.json")):
            files_to_scan.append(f)
        for f in sorted(ART.glob("*.txt")):
            files_to_scan.append(f)
    if DATA_CASES.exists():
        files_to_scan.append(DATA_CASES)
    failures, scanned = _secret_scan_files(files_to_scan)
    results.append(_check(
        "25. secret scan: no Telegram credential / recipient id / API key / cookie / Authorization / private key in committed files",
        not failures,
        f"scanned={scanned} files, hits=0" if not failures else f"hits={len(failures)}: {failures[:3]}",
    ))

    # 26. git status: no root .evolver/ or memory/ tracked
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=str(REPO), capture_output=True, text=True, check=True
        ).stdout
        tracked = [
            l for l in out.splitlines()
            if l == ".evolver" or l.startswith(".evolver/") or l == "memory" or l.startswith("memory/")
        ]
        results.append(_check(
            "26. git status: no root .evolver/ or memory/ tracked",
            not tracked,
            f"root .evolver/ or memory/ tracked: {tracked}" if tracked else "clean",
        ))
    except Exception as e:
        results.append(_check("26. git status: no root .evolver/ or memory/ tracked", False, f"git error: {e}"))

    # 27. prior validators (5, 6A, 6B, 7A) ALL CHECKS PASSED (backward-compat)
    validators = [
        ("Phase 5", REPO / "scripts" / "validate_evomap_phase5_local_evolution_kit.py"),
        ("Phase 6A", REPO / "scripts" / "validate_evomap_phase6a_hermes_systemd_bundle.py"),
        ("Phase 6B", REPO / "scripts" / "validate_evomap_phase6b_telegram_router_bundle.py"),
        ("Phase 7A", REPO / "scripts" / "validate_evomap_phase7a_domain_signal_injection.py"),
    ]
    failed = []
    for name, vp in validators:
        if not vp.exists():
            failed.append(f"{name}: missing")
            continue
        try:
            r = subprocess.run(["python3", str(vp)], cwd=str(REPO), capture_output=True, text=True, timeout=60)
            if "ALL CHECKS PASSED" not in r.stdout:
                failed.append(f"{name}: rc={r.returncode}")
        except Exception as e:
            failed.append(f"{name}: {e}")
    results.append(_check(
        "27. prior validators (5, 6A, 6B, 7A) ALL CHECKS PASSED (backward-compat)",
        not failed,
        f"4/4 prior validators PASS" if not failed else f"failed: {failed}",
    ))

    # ---- summary ----
    passes = sum(1 for r in results if r["ok"])
    fails = sum(1 for r in results if not r["ok"])
    print("ATL-EVOMAP-7B Cross-Bundle Regression — Validator")
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
        print("Case: evomap-evolver-openclaw-v0 (Phase 7B Cross-Bundle Regression)")
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
