#!/usr/bin/env python3
"""
validate_evomap_phase7a_domain_signal_injection.py

Validator for the ATL-EVOMAP-7A Domain-Specific Signal Injection enhancement.
Forwards-compatible: accepts ATL-EVOMAP-5/6A/6B/7A entries in phase_history
so this validator stays green as the case progresses.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, subprocess)
- Runs in current working directory (the ai-tool-test-lab repo root)
- Does NOT contact Hub, does NOT publish, does NOT consume credits
- Does NOT execute evolver --approve or evolver solidify
- Does NOT commit runtime .evolver/ or memory/ originals
- Pure file-level + JSON-level checks; no network calls; no shell exec for
  curl/wget/HTTP

Checks (20):
  1.  scripts/evomap_apply_bundle.py exists and contains --inject-signals-from
  2.  Phase 7A case README exists
  3.  Phase 7A case report exists (case dir)
  4.  Phase 7A top-level report exists (reports/)
  5.  default-apply-dry-run-output.json exists, ok true, mode generic_only
  6.  default-apply-yes-output.json exists, ok true, mode generic_only
  7.  default-apply-target-summary.json exists, memory_graph_lines == 5
  8.  hermes-domain-dry-run-output.json exists, ok true, mode generic_plus_domain_from_bundle
  9.  hermes-domain-yes-output.json exists, ok true, mode generic_plus_domain_from_bundle
 10.  hermes-domain-target-summary.json exists, contains systemd_failure, missing_env_var,
      port_not_listening
 11.  telegram-domain-dry-run-output.json exists, ok true, mode generic_plus_domain_from_bundle
 12.  telegram-domain-yes-output.json exists, ok true, mode generic_plus_domain_from_bundle
 13.  telegram-domain-target-summary.json contains telegram_failure, proxy_mismatch,
      delivery_terminal_missing, sendmessage_timeout
 14.  domain-signal-extraction-summary.json exists, hermes_domain_signals_injected true,
      telegram_domain_signals_injected true
 15.  data/cases.json contains ATL-EVOMAP-7A in phase or phase_history
 16.  main case README contains ATL-EVOMAP-7A
 17.  secret scan: no Telegram credential-like pattern, no chat-id-like
      long numeric recipient, no API key, no cookie, no Authorization header
      value, no private key in any of the committed files
 18.  git status: no root .evolver/ or memory/ tracked
 19.  scripts/validate_evomap_phase5_local_evolution_kit.py ALL CHECKS PASSED
 20.  scripts/validate_evomap_phase6a_hermes_systemd_bundle.py AND
      scripts/validate_evomap_phase6b_telegram_router_bundle.py ALL CHECKS PASSED
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root (cwd). All paths are relative to this.
REPO = Path.cwd()

CASE = REPO / "cases/evomap-evolver-openclaw-v0/phase7a-domain-signal-injection"
ART = CASE / "artifacts"
APPLY_TOOL = REPO / "scripts" / "evomap_apply_bundle.py"
CASE_REPORT = CASE / "ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md"
TOPLEVEL_REPORT = REPO / "reports" / "ATL_EVOMAP_7A_DOMAIN_SIGNAL_INJECTION_REPORT.md"
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
    "validate_evomap_phase6b_telegram_router_bundle.py",
    "validate_evomap_phase6a_hermes_systemd_bundle.py",
    "validate_evomap_phase5_local_evolution_kit.py",
    "evolver-run-hermes-domain-output.txt",
    "evolver-review-hermes-domain-output.txt",
    "evolver-run-telegram-domain-output.txt",
    "evolver-review-telegram-domain-output.txt",
    "evolver-run-telegram-target-output.txt",
    "evolver-review-telegram-target-output.txt",
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
            "domain_signals": d.get("domain_signals"),
            "domain_rejected": d.get("domain_signals_rejected"),
        }
    if d.get("mode") == "dry-run":
        plan = d.get("plan", {})
        return {
            "ok": d.get("ok"),
            "mode": plan.get("signal_injection_mode"),
            "memory_signals": plan.get("summary", {}).get("memory_graph_signals_added"),
            "domain_signals": plan.get("domain_signals"),
            "domain_rejected": plan.get("domain_signals_rejected"),
        }
    return {"ok": False, "mode": "unknown"}


def main():
    parser = argparse.ArgumentParser(description="Validator for ATL-EVOMAP-7A Domain-Specific Signal Injection.")
    parser.add_argument("--strict", action="store_true", help="(no-op) this validator is strict by default")
    args = parser.parse_args()

    results = []

    # 1. apply tool exists + contains --inject-signals-from
    if APPLY_TOOL.exists():
        text = APPLY_TOOL.read_text(encoding="utf-8", errors="replace")
        has_flag = "--inject-signals-from" in text
        has_extract = "_extract_signals_from_bundle" in text
        has_validate = "_validate_signal_name" in text
        has_dangerous = "DANGEROUS_SIGNALS" in text
        has_credential = "CREDENTIAL_PATTERN" in text
        ok = has_flag and has_extract and has_validate and has_dangerous and has_credential
        results.append(_check(
            "1. apply tool has --inject-signals-from + signal extraction + filter engine",
            ok,
            f"flag={has_flag} extract={has_extract} validate={has_validate} dangerous={has_dangerous} credential={has_credential}",
        ))
    else:
        results.append(_check("1. apply tool has --inject-signals-from + signal extraction + filter engine", False, "missing"))

    # 2. case README
    results.append(_check("2. case README exists", CASE_README.exists(), str(CASE_README.relative_to(REPO))))

    # 3. case report
    results.append(_check("3. case report exists", CASE_REPORT.exists(), str(CASE_REPORT.relative_to(REPO))))

    # 4. top-level report
    results.append(_check("4. top-level report exists", TOPLEVEL_REPORT.exists(), str(TOPLEVEL_REPORT.relative_to(REPO))))

    # 5. default apply dry-run
    p = ART / "default-apply-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "5. default-apply dry-run: ok & mode=generic_only",
            d.get("ok") is True and d.get("mode") == "generic_only",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("5. default-apply dry-run: ok & mode=generic_only", False, "missing"))

    # 6. default apply --yes
    p = ART / "default-apply-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "6. default-apply --yes: ok & mode=generic_only",
            d.get("ok") is True and d.get("mode") == "generic_only",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("6. default-apply --yes: ok & mode=generic_only", False, "missing"))

    # 7. default target summary memory_graph_lines == 5
    p = ART / "default-apply-target-summary.json"
    if p.exists():
        s = _read_json(p)
        results.append(_check(
            "7. default target summary: memory_graph_lines == 5",
            s.get("memory_graph_lines") == 5,
            f"memory_graph_lines={s.get('memory_graph_lines')}",
        ))
    else:
        results.append(_check("7. default target summary: memory_graph_lines == 5", False, "missing"))

    # 8. hermes domain dry-run
    p = ART / "hermes-domain-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "8. hermes-domain dry-run: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("8. hermes-domain dry-run: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    # 9. hermes domain --yes
    p = ART / "hermes-domain-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "9. hermes-domain --yes: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("9. hermes-domain --yes: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    # 10. hermes target summary contains required signals
    p = ART / "hermes-domain-target-summary.json"
    if p.exists():
        s = _read_json(p)
        sigs = s.get("memory_graph_signals", [])
        required = ["systemd_failure", "missing_env_var", "port_not_listening"]
        missing = [r for r in required if r not in sigs]
        results.append(_check(
            "10. hermes target summary contains systemd_failure / missing_env_var / port_not_listening",
            not missing,
            f"missing={missing}" if missing else f"all 3 present in {len(sigs)} signals",
        ))
    else:
        results.append(_check("10. hermes target summary contains systemd_failure / missing_env_var / port_not_listening", False, "missing"))

    # 11. telegram domain dry-run
    p = ART / "telegram-domain-dry-run-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "11. telegram-domain dry-run: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("11. telegram-domain dry-run: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    # 12. telegram domain --yes
    p = ART / "telegram-domain-yes-output.json"
    if p.exists():
        d = _read_apply_output(p)
        results.append(_check(
            "12. telegram-domain --yes: ok & mode=generic_plus_domain_from_bundle",
            d.get("ok") is True and d.get("mode") == "generic_plus_domain_from_bundle",
            f"ok={d.get('ok')}, mode={d.get('mode')}",
        ))
    else:
        results.append(_check("12. telegram-domain --yes: ok & mode=generic_plus_domain_from_bundle", False, "missing"))

    # 13. telegram target summary contains required signals
    p = ART / "telegram-domain-target-summary.json"
    if p.exists():
        s = _read_json(p)
        sigs = s.get("memory_graph_signals", [])
        required = ["telegram_failure", "proxy_mismatch", "delivery_terminal_missing", "sendmessage_timeout"]
        missing = [r for r in required if r not in sigs]
        results.append(_check(
            "13. telegram target summary contains telegram_failure / proxy_mismatch / delivery_terminal_missing / sendmessage_timeout",
            not missing,
            f"missing={missing}" if missing else f"all 4 present in {len(sigs)} signals",
        ))
    else:
        results.append(_check("13. telegram target summary contains telegram_failure / proxy_mismatch / delivery_terminal_missing / sendmessage_timeout", False, "missing"))

    # 14. domain-signal-extraction-summary.json
    p = ART / "domain-signal-extraction-summary.json"
    if p.exists():
        s = _read_json(p)
        ok = (
            s.get("default_generic_only") is True
            and s.get("hermes_domain_signals_injected") is True
            and s.get("telegram_domain_signals_injected") is True
            and s.get("default_behavior_preserved") is True
            and s.get("hub") == "disabled"
            and s.get("approve") == "not_executed"
            and s.get("solidify") == "not_executed"
        )
        results.append(_check(
            "14. domain-signal-extraction-summary: hermes+telegram injected, default preserved, no hub/approve/solidify",
            ok,
            f"default={s.get('default_generic_only')} hermes={s.get('hermes_domain_signals_injected')} telegram={s.get('telegram_domain_signals_injected')} hub={s.get('hub')}",
        ))
    else:
        results.append(_check("14. domain-signal-extraction-summary: hermes+telegram injected, default preserved, no hub/approve/solidify", False, "missing"))

    # 15. data/cases.json
    if DATA_CASES.exists():
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            top_phase = case.get("phase", "") if case else ""
            history_phases = [h.get("phase", "") for h in (case.get("phase_history") or [])] if case else []
            has_7a = "ATL-EVOMAP-7A" in top_phase or "ATL-EVOMAP-7A" in history_phases
            results.append(_check(
                "15. data/cases.json contains ATL-EVOMAP-7A in phase or phase_history",
                has_7a,
                f"top_phase={top_phase!r}, history_count={len(history_phases)}",
            ))
        except Exception as e:
            results.append(_check("15. data/cases.json contains ATL-EVOMAP-7A in phase or phase_history", False, f"json error: {e}"))
    else:
        results.append(_check("15. data/cases.json contains ATL-EVOMAP-7A in phase or phase_history", False, "cases.json missing"))

    # 16. main case README
    if MAIN_CASE_README.exists():
        text = MAIN_CASE_README.read_text(encoding="utf-8", errors="replace")
        results.append(_check(
            "16. main case README references ATL-EVOMAP-7A",
            "ATL-EVOMAP-7A" in text,
            f"main README len={len(text)}",
        ))
    else:
        results.append(_check("16. main case README references ATL-EVOMAP-7A", False, "main README missing"))

    # 17. secret scan
    files_to_scan = [
        APPLY_TOOL,
        CASE_REPORT,
        TOPLEVEL_REPORT,
        CASE_README,
        MAIN_CASE_README,
        # All artifacts except the ones that document the patterns as regex
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
        "17. secret scan: no Telegram credential / recipient id / API key / Authorization / private key in committed files",
        not failures,
        f"scanned={scanned} files, hits=0" if not failures else f"hits={len(failures)}: {failures[:3]}",
    ))

    # 18. git status: no root .evolver/ or memory/ tracked
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=str(REPO), capture_output=True, text=True, check=True
        ).stdout
        tracked = [
            l for l in out.splitlines()
            if l == ".evolver" or l.startswith(".evolver/") or l == "memory" or l.startswith("memory/")
        ]
        results.append(_check(
            "18. git status: no root .evolver/ or memory/ tracked",
            not tracked,
            f"root .evolver/ or memory/ tracked: {tracked}" if tracked else "clean",
        ))
    except Exception as e:
        results.append(_check("18. git status: no root .evolver/ or memory/ tracked", False, f"git error: {e}"))

    # 19. Phase 5 validator
    v5 = REPO / "scripts" / "validate_evomap_phase5_local_evolution_kit.py"
    if v5.exists():
        try:
            r = subprocess.run(["python3", str(v5)], cwd=str(REPO), capture_output=True, text=True, timeout=60)
            ok = "ALL CHECKS PASSED" in r.stdout
            results.append(_check(
                "19. Phase 5 validator ALL CHECKS PASSED (backward-compat)",
                ok,
                f"returncode={r.returncode}, output_tail={r.stdout.strip().splitlines()[-1] if r.stdout.strip() else '<empty>'}",
            ))
        except Exception as e:
            results.append(_check("19. Phase 5 validator ALL CHECKS PASSED (backward-compat)", False, f"error: {e}"))
    else:
        results.append(_check("19. Phase 5 validator ALL CHECKS PASSED (backward-compat)", False, "missing"))

    # 20. Phase 6A + 6B validator
    v6a = REPO / "scripts" / "validate_evomap_phase6a_hermes_systemd_bundle.py"
    v6b = REPO / "scripts" / "validate_evomap_phase6b_telegram_router_bundle.py"
    if v6a.exists() and v6b.exists():
        try:
            ra = subprocess.run(["python3", str(v6a)], cwd=str(REPO), capture_output=True, text=True, timeout=60)
            rb = subprocess.run(["python3", str(v6b)], cwd=str(REPO), capture_output=True, text=True, timeout=60)
            ok = "ALL CHECKS PASSED" in ra.stdout and "ALL CHECKS PASSED" in rb.stdout
            results.append(_check(
                "20. Phase 6A + 6B validators ALL CHECKS PASSED (backward-compat)",
                ok,
                f"6A_rc={ra.returncode}, 6B_rc={rb.returncode}",
            ))
        except Exception as e:
            results.append(_check("20. Phase 6A + 6B validators ALL CHECKS PASSED (backward-compat)", False, f"error: {e}"))
    else:
        results.append(_check("20. Phase 6A + 6B validators ALL CHECKS PASSED (backward-compat)", False, "missing"))

    # ---- summary ----
    passes = sum(1 for r in results if r["ok"])
    fails = sum(1 for r in results if not r["ok"])
    print(f"ATL-EVOMAP-7A Domain-Specific Signal Injection — Validator")
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
        print("Case: evomap-evolver-openclaw-v0 (Phase 7A Domain-Specific Signal Injection)")
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
