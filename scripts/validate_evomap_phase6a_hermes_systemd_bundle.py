#!/usr/bin/env python3
"""
validate_evomap_phase6a_hermes_systemd_bundle.py

Validates ATL-EVOMAP-6A Hermes Systemd Service Recovery Bundle.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.

Checks (19):
  1. Phase 6A README exists
  2. Phase 6A case report exists
  3. Top-level Phase 6A report exists
  4. fixtures/hermes-systemd-failure-sample.txt exists and non-empty
  5. bundle/hermes-systemd-service-recovery.bundle.json exists and is valid JSON
  6. scripts/hermes_systemd_recovery_fixture.py exists
  7. artifacts/gene-hermes-systemd-service-recovery.json exists and valid JSON
  8. artifacts/capsule-hermes-systemd-service-recovery.json exists and valid JSON
  9. artifacts/hermes-systemd-fixture-output.json has missing_env_var=MODEL_PROVIDER
 10. artifacts/inspect-bundle-output.json ok=true
 11. artifacts/validate-bundle-output.json ok=true, secret_hits=0, 12+ checks
 12. artifacts/apply-bundle-dry-run-output.json mode='dry-run'
 13. artifacts/apply-bundle-yes-output.json mode='applied'
 14. artifacts/apply-target-summary.json gene_count>=1, capsule_count>=1, memory_graph_lines>=5
 15. case tools/ has 3 script copies
 16. data/cases.json phase contains ATL-EVOMAP-6A and phase_history entry exists
 17. case README contains ATL-EVOMAP-6A
 18. secret scan PASS across Phase 6A artifacts (no sk-/xoxb-/Bearer/etc.)
 19. git status: no root .evolver/ or memory/ tracked (forward-compat with Phase 5)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase6a-hermes-systemd-bundle"
BUNDLE_ARTIFACTS = BUNDLE_DIR / "artifacts"
BUNDLE_BUNDLE = BUNDLE_DIR / "bundle" / "hermes-systemd-service-recovery.bundle.json"
BUNDLE_FIXTURE = BUNDLE_DIR / "fixtures" / "hermes-systemd-failure-sample.txt"
BUNDLE_TOOLS = BUNDLE_DIR / "tools"
BUNDLE_README = BUNDLE_DIR / "README.md"
BUNDLE_REPORT = BUNDLE_DIR / "ATL_EVOMAP_6A_HERMES_SYSTEMD_BUNDLE_REPORT.md"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_6A_HERMES_SYSTEMD_BUNDLE_REPORT.md"
CASE_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

PARSER_SCRIPT = REPO_ROOT / "scripts" / "hermes_systemd_recovery_fixture.py"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{16,}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]{16,}"),
    re.compile(r"bot[0-9]{6,}:[A-Za-z0-9_-]{20,}"),
    re.compile(r"[0-9]{8,}:[A-Za-z0-9_-]{20,}"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
    re.compile(r"C:\\Users\\[A-Za-z0-9_. -]+\\"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _info(msg: str) -> None:
    print(f"\033[94mINFO\033[0m  {msg}")


def _ok(msg: str) -> None:
    print(f"\033[92mPASS\033[0m  {msg}")


def _fail(msg: str) -> None:
    print(f"\033[91mFAIL\033[0m  {msg}", file=sys.stderr)


_failures = 0


def _check(name: str, condition: bool, message: str = "") -> bool:
    global _failures
    if condition:
        _ok(name + (f" — {message}" if message else ""))
        return True
    _failures += 1
    _fail(name + (f" — {message}" if message else ""))
    return False


def main() -> int:
    print("=" * 60)
    print("ATL-EVOMAP-6A Hermes Systemd Bundle Validator")
    print("=" * 60)

    # 1. Phase 6A README exists
    _info("1. Checking Phase 6A README exists...")
    _check("Phase 6A README exists", BUNDLE_README.is_file())

    # 2. Phase 6A case report exists
    _info("2. Checking Phase 6A case report exists...")
    _check("Phase 6A case report exists", BUNDLE_REPORT.is_file())

    # 3. Top-level Phase 6A report exists
    _info("3. Checking top-level Phase 6A report exists...")
    _check("top-level Phase 6A report exists", TOP_REPORT.is_file())

    # 4. Fixture exists and non-empty
    _info("4. Checking fixtures/hermes-systemd-failure-sample.txt exists and non-empty...")
    _check(
        "fixture exists and >= 500 bytes",
        BUNDLE_FIXTURE.is_file() and BUNDLE_FIXTURE.stat().st_size >= 500,
        f"{BUNDLE_FIXTURE.stat().st_size} bytes" if BUNDLE_FIXTURE.exists() else "missing",
    )
    # Fixture must declare hard rules
    if BUNDLE_FIXTURE.is_file():
        text = BUNDLE_FIXTURE.read_text()
        for needle in ("Do not print secrets", "Do not read .env",
                       "Do not restart real service", "Only parse this text"):
            _check(f"fixture contains hard rule: '{needle}'", needle in text)

    # 5. bundle exists and valid JSON
    _info("5. Checking bundle/hermes-systemd-service-recovery.bundle.json exists and is valid JSON...")
    bundle = None
    if not BUNDLE_BUNDLE.is_file():
        _check("canonical bundle exists", False)
    else:
        _check("canonical bundle exists", True)
        try:
            bundle = json.loads(BUNDLE_BUNDLE.read_text())
            _check("canonical bundle is valid JSON", True)
        except Exception as e:
            _check("canonical bundle is valid JSON", False, str(e))
    if bundle is not None:
        _check("bundle has 'gene' field", "gene" in bundle)
        _check("bundle has 'capsule' field", "capsule" in bundle)
        _check("bundle has 'execution_trace' field", "execution_trace" in bundle)
        _check("bundle has 'safety' field", "safety" in bundle)
        _check("bundle has 'import_contract' field", "import_contract" in bundle)
        _check("bundle has 'fixture_summary' field (Phase 6A addition)",
               "fixture_summary" in bundle)
        _check("bundle source_phase == 'ATL-EVOMAP-6A'",
               bundle.get("source_phase") == "ATL-EVOMAP-6A")
        if "safety" in bundle:
            safety = bundle["safety"]
            for k in ["hub", "publish", "credits", "visibility",
                      "no_failed_events", "no_pollution_signals",
                      "no_real_system_mutation"]:
                _check(f"safety.{k} present", k in safety)
            _check("safety.hub == 'disabled'", safety.get("hub") == "disabled")
            _check("safety.publish == 'disabled'", safety.get("publish") == "disabled")
            _check("safety.credits == 0", safety.get("credits") == 0)
        if "fixture_summary" in bundle:
            fs = bundle["fixture_summary"]
            _check("fixture_summary.expected_missing_env_var == MODEL_PROVIDER",
                   fs.get("expected_missing_env_var") == "MODEL_PROVIDER")
            _check("fixture_summary.expected_service == hermes-gateway.service",
                   fs.get("expected_service") == "hermes-gateway.service")
            _check("fixture_summary.expected_port == 127.0.0.1:18789",
                   fs.get("expected_port") == "127.0.0.1:18789")
            for k in ("no_real_systemctl", "no_real_journalctl",
                      "no_env_scan", "no_secrets"):
                _check(f"fixture_summary.{k} == True", fs.get(k) is True)

    # 6. Offline parser exists
    _info("6. Checking scripts/hermes_systemd_recovery_fixture.py exists...")
    _check("scripts/hermes_systemd_recovery_fixture.py exists", PARSER_SCRIPT.is_file())
    # Must use stdlib only
    if PARSER_SCRIPT.is_file():
        text = PARSER_SCRIPT.read_text()
        for forbidden_import in ("import requests", "import urllib", "import urllib3",
                                 "import yaml", "import httpx", "import aiohttp"):
            _check(f"parser does NOT import {forbidden_import}",
                   forbidden_import not in text)
        _check("parser uses argparse", "argparse" in text)
        _check("parser uses json", "import json" in text)
        _check("parser uses re", "import re" in text)

    # 7. Gene artifact exists and valid JSON
    _info("7. Checking artifacts/gene-hermes-systemd-service-recovery.json exists and valid JSON...")
    gene_out = BUNDLE_ARTIFACTS / "gene-hermes-systemd-service-recovery.json"
    if gene_out.is_file():
        try:
            gene = json.loads(gene_out.read_text())
            _check("gene artifact is valid JSON", True)
            _check("gene.type == 'Gene'", gene.get("type") == "Gene")
            _check("gene.id == 'gene_distilled_hermes-systemd-service-recovery'",
                   gene.get("id") == "gene_distilled_hermes-systemd-service-recovery")
            _check("gene.category == 'repair'", gene.get("category") == "repair")
            sigs = gene.get("signals_match", [])
            _check("gene.signals_match has >= 5 entries", len(sigs) >= 5,
                   f"{len(sigs)} signals")
            _check("gene.signals_match has bare + qualified forms",
                   "systemd_failure" in sigs and any(":" in s for s in sigs))
            strat = gene.get("strategy", [])
            _check("gene.strategy has >= 3 steps", len(strat) >= 3,
                   f"{len(strat)} steps")
        except Exception as e:
            _check("gene artifact is valid JSON", False, str(e))
    else:
        _check("gene artifact exists", False)

    # 8. Capsule artifact exists and valid JSON
    _info("8. Checking artifacts/capsule-hermes-systemd-service-recovery.json exists and valid JSON...")
    cap_out = BUNDLE_ARTIFACTS / "capsule-hermes-systemd-service-recovery.json"
    if cap_out.is_file():
        try:
            cap = json.loads(cap_out.read_text())
            _check("capsule artifact is valid JSON", True)
            _check("capsule.type == 'Capsule'", cap.get("type") == "Capsule")
            _check("capsule.id == 'capsule_hermes_systemd_service_recovery_phase6a'",
                   cap.get("id") == "capsule_hermes_systemd_service_recovery_phase6a")
            _check("capsule.gene matches Gene id",
                   cap.get("gene") == "gene_distilled_hermes-systemd-service-recovery")
            trace = cap.get("execution_trace", [])
            _check("capsule.execution_trace is non-empty list",
                   isinstance(trace, list) and len(trace) >= 1,
                   f"len={len(trace)}")
            stages = [s.get("stage") for s in trace]
            for st in ("build", "validate", "canary"):
                _check(f"capsule.execution_trace has stage '{st}'", st in stages)
            # Canary check must include 8 canaries all true
            canary_steps = [s for s in trace if s.get("stage") == "canary"]
            if canary_steps:
                checks = canary_steps[0].get("checks", {})
                for k in ("no_real_systemctl", "no_real_journalctl", "no_env_scan",
                          "no_secrets", "no_hub", "no_publish", "no_approve",
                          "no_solidify"):
                    _check(f"capsule canary checks.{k} == True",
                           checks.get(k) is True)
        except Exception as e:
            _check("capsule artifact is valid JSON", False, str(e))
    else:
        _check("capsule artifact exists", False)

    # 9. Parser output exists and has expected failure shape
    _info("9. Checking hermes-systemd-fixture-output.json has expected failure shape...")
    fix_out = BUNDLE_ARTIFACTS / "hermes-systemd-fixture-output.json"
    if fix_out.is_file():
        try:
            fix = json.loads(fix_out.read_text())
            _check("parser output ok=true", fix.get("ok") is True)
            _check("parser output service == hermes-gateway.service",
                   fix.get("service") == "hermes-gateway.service")
            _check("parser output service_failed == True",
                   fix.get("service_failed") is True)
            _check("parser output missing_env_var == MODEL_PROVIDER",
                   fix.get("missing_env_var") == "MODEL_PROVIDER")
            _check("parser output expected_port == 127.0.0.1:18789",
                   fix.get("expected_port") == "127.0.0.1:18789")
            _check("parser output port_not_listening == True",
                   fix.get("port_not_listening") is True)
            rco = fix.get("recommended_check_order", [])
            _check("parser output recommended_check_order has >= 5 steps",
                   len(rco) >= 5, f"{len(rco)} steps")
            safety = fix.get("safety", {})
            for k in ("no_real_systemctl", "no_real_journalctl",
                      "no_env_scan", "no_secrets", "no_network_call", "no_repo_scan"):
                _check(f"parser output safety.{k} == True", safety.get(k) is True)
        except Exception as e:
            _check("parser output valid JSON", False, str(e))
    else:
        _check("parser output exists", False)

    # 10. inspect-bundle-output.json ok=true
    _info("10. Checking inspect-bundle-output.json exists and ok=true...")
    inspect_out = BUNDLE_ARTIFACTS / "inspect-bundle-output.json"
    if inspect_out.is_file():
        try:
            d = json.loads(inspect_out.read_text())
            _check("inspect-bundle-output.json ok=true", d.get("ok") is True)
            _check("inspect reports gene_id matches",
                   d.get("gene_id") == "gene_distilled_hermes-systemd-service-recovery")
            _check("inspect reports capsule_id matches",
                   d.get("capsule_id") == "capsule_hermes_systemd_service_recovery_phase6a")
            _check("inspect reports execution_trace_steps >= 4",
                   d.get("execution_trace_steps", 0) >= 4,
                   str(d.get("execution_trace_steps")))
        except Exception as e:
            _check("inspect-bundle-output.json valid JSON", False, str(e))
    else:
        _check("inspect-bundle-output.json exists", False)

    # 11. validate-bundle-output.json ok=true, secret_hits=0
    _info("11. Checking validate-bundle-output.json exists and ok=true with secret_hits=0...")
    validate_out = BUNDLE_ARTIFACTS / "validate-bundle-output.json"
    if validate_out.is_file():
        try:
            d = json.loads(validate_out.read_text())
            _check("validate-bundle-output.json ok=true", d.get("ok") is True)
            _check("validate-bundle-output.json has 0 failures",
                   len(d.get("failures", [])) == 0)
            n_checks = len(d.get("checks", []))
            n_pass = sum(1 for c in d.get("checks", []) if c.get("ok"))
            _check(f"validate-bundle-output.json has 12+ checks all pass",
                   n_checks >= 12 and n_pass == n_checks, f"{n_pass}/{n_checks} pass")
            _check("validate-bundle-output.json secret_hits == 0",
                   d.get("summary", {}).get("secret_hits") == 0)
        except Exception as e:
            _check("validate-bundle-output.json valid JSON", False, str(e))
    else:
        _check("validate-bundle-output.json exists", False)

    # 12. apply-bundle-dry-run-output.json mode='dry-run'
    _info("12. Checking apply-bundle-dry-run-output.json mode='dry-run'...")
    dry_run_out = BUNDLE_ARTIFACTS / "apply-bundle-dry-run-output.json"
    if dry_run_out.is_file():
        try:
            d = json.loads(dry_run_out.read_text())
            _check("apply-dry-run mode='dry-run'", d.get("mode") == "dry-run")
            _check("apply-dry-run ok=true", d.get("ok") is True)
            summary = d.get("plan", {}).get("summary", {})
            _check("apply-dry-run new_gene_count >= 1",
                   summary.get("new_gene_count", 0) >= 1,
                   str(summary.get("new_gene_count")))
            _check("apply-dry-run new_capsule_count >= 1",
                   summary.get("new_capsule_count", 0) >= 1,
                   str(summary.get("new_capsule_count")))
            _check("apply-dry-run memory_graph_signals_added >= 5",
                   summary.get("memory_graph_signals_added", 0) >= 5,
                   str(summary.get("memory_graph_signals_added")))
        except Exception as e:
            _check("apply-dry-run valid JSON", False, str(e))
    else:
        _check("apply-bundle-dry-run-output.json exists", False)

    # 13. apply-bundle-yes-output.json mode='applied'
    _info("13. Checking apply-bundle-yes-output.json mode='applied'...")
    yes_out = BUNDLE_ARTIFACTS / "apply-bundle-yes-output.json"
    if yes_out.is_file():
        try:
            d = json.loads(yes_out.read_text())
            _check("apply-yes mode='applied'", d.get("mode") == "applied")
            _check("apply-yes ok=true", d.get("ok") is True)
            _check("apply-yes 0 errors",
                   len(d.get("log", {}).get("errors", [])) == 0)
            n_writes = len(d.get("log", {}).get("writes_executed", []))
            _check(f"apply-yes wrote >= 6 files",
                   n_writes >= 6, f"{n_writes} files")
        except Exception as e:
            _check("apply-yes valid JSON", False, str(e))
    else:
        _check("apply-bundle-yes-output.json exists", False)

    # 14. apply-target-summary.json counts
    _info("14. Checking apply-target-summary.json has valid counts...")
    summary_out = BUNDLE_ARTIFACTS / "apply-target-summary.json"
    if summary_out.is_file():
        try:
            d = json.loads(summary_out.read_text())
            _check("summary.gene_count >= 1", d.get("gene_count", 0) >= 1,
                   str(d.get("gene_count")))
            _check("summary.capsule_count >= 1", d.get("capsule_count", 0) >= 1,
                   str(d.get("capsule_count")))
            _check("summary.memory_graph_lines >= 5",
                   d.get("memory_graph_lines", 0) >= 5,
                   str(d.get("memory_graph_lines")))
            gene_ids = d.get("gene_ids", [])
            cap_ids = d.get("capsule_ids", [])
            _check("summary.gene_ids contains Hermes gene",
                   "gene_distilled_hermes-systemd-service-recovery" in gene_ids)
            _check("summary.capsule_ids contains Hermes capsule",
                   "capsule_hermes_systemd_service_recovery_phase6a" in cap_ids)
        except Exception as e:
            _check("apply-target-summary.json valid JSON", False, str(e))
    else:
        _check("apply-target-summary.json exists", False)

    # 15. Case tools/ has 3 script copies
    _info("15. Checking case tools/ has 3 script copies...")
    for tool in ("evomap_inspect_bundle.py", "evomap_validate_bundle.py",
                 "evomap_apply_bundle.py"):
        _check(f"case tools/{tool} exists", (BUNDLE_TOOLS / tool).is_file())

    # 16. data/cases.json phase + phase_history
    _info("16. Checking data/cases.json phase + phase_history for ATL-EVOMAP-6A...")
    if CASES_JSON.is_file():
        try:
            data = json.loads(CASES_JSON.read_text())
            case = next(
                (c for c in data["cases"] if c.get("slug") == "evomap-evolver-openclaw-v0"),
                None,
            )
            if case is None:
                _check("evomap case present in cases.json", False)
            else:
                _check("evomap case present in cases.json", True)
                # Forward-compat: accept ATL-EVOMAP-6A in either the top-level
                # phase or the phase_history. This lets the case advance
                # (e.g. 6A → 6B) without re-running 6A-specific assertions
                # on stale top-level fields.
                hist = case.get("phase_history", [])
                has_6a = any(e.get("phase") == "ATL-EVOMAP-6A" for e in hist)
                phase_match = "ATL-EVOMAP-6A" in case.get("phase", "") or has_6a
                status_match = (
                    "hermes systemd bundle completed" in case.get("status", "")
                    or has_6a
                )
                final_status_match = (
                    "HERMES_SYSTEMD_BUNDLE_PASS" in case.get("final_status", "")
                    or has_6a
                )
                _check("cases.json phase contains ATL-EVOMAP-6A (top-level or phase_history)",
                       phase_match,
                       case.get("phase", ""))
                _check("cases.json status contains 'hermes systemd bundle completed' (or phase_history has 6A)",
                       status_match,
                       case.get("status", ""))
                _check("cases.json final_status contains HERMES_SYSTEMD_BUNDLE_PASS (or phase_history has 6A)",
                       final_status_match,
                       case.get("final_status", ""))
                _check("cases.json phase_history has ATL-EVOMAP-6A entry", has_6a)
                if has_6a:
                    last6a = next(e for e in hist if e.get("phase") == "ATL-EVOMAP-6A")
                    _check("phase_history ATL-EVOMAP-6A result == PASS",
                           last6a.get("result") == "PASS")
                    _check("phase_history ATL-EVOMAP-6A has gene_id",
                           last6a.get("gene_id") == "gene_distilled_hermes-systemd-service-recovery")
                    _check("phase_history ATL-EVOMAP-6A has capsule_id",
                           last6a.get("capsule_id") == "capsule_hermes_systemd_service_recovery_phase6a")
                    _check("phase_history ATL-EVOMAP-6A has evolver_smoke",
                           isinstance(last6a.get("evolver_smoke"), dict))
        except Exception as e:
            _check("cases.json valid JSON", False, str(e))
    else:
        _check("data/cases.json exists", False)

    # 17. case README contains ATL-EVOMAP-6A
    _info("17. Checking case README contains ATL-EVOMAP-6A...")
    if CASE_README.is_file():
        text = CASE_README.read_text()
        _check("case README contains ATL-EVOMAP-6A", "ATL-EVOMAP-6A" in text)
        _check("case README contains '6A' row in phase table",
               "**6A**" in text or "| **6A**" in text)
    else:
        _check("case README exists", False)

    # 18. Secret scan
    _info("18. Scanning for secret patterns in Phase 6A artifacts...")
    scan_paths = [
        BUNDLE_ARTIFACTS, BUNDLE_BUNDLE, BUNDLE_FIXTURE, BUNDLE_README,
        BUNDLE_REPORT, TOP_REPORT, CASE_README, CASES_JSON, BUNDLE_TOOLS,
        PARSER_SCRIPT,
    ]
    secret_hits = []
    for path in scan_paths:
        if not path.exists():
            continue
        if path.is_dir():
            for p in path.rglob("*"):
                if p.is_file() and p.suffix in {".txt", ".json", ".jsonl", ".md", ".py"}:
                    try:
                        content = p.read_text(errors="ignore")
                    except Exception:
                        continue
                    for pat in SECRET_PATTERNS:
                        if pat.search(content):
                            secret_hits.append((p, pat.pattern))
        else:
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(content):
                    secret_hits.append((path, pat.pattern))

    if not secret_hits:
        _check("no secret patterns in Phase 6A artifacts", True)
    else:
        for p, pat in secret_hits:
            _check(f"no secret pattern '{pat}' in {p.name}", False)

    # 19. No root .evolver/ or memory/ tracked by git (forward-compat with Phase 5)
    _info("19. Checking no root .evolver/ or memory/ tracked by git...")
    try:
        result = subprocess.run(
            ["git", "ls-files", ".evolver/", "memory/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = [line for line in result.stdout.splitlines() if line.strip()]
        non_keep = [t for t in tracked if not t.endswith(".gitkeep")]
        _check(
            "no root .evolver/ or memory/ tracked by git",
            len(non_keep) == 0,
            f"tracked: {non_keep[:3]}" if non_keep else "clean",
        )
    except Exception as e:
        _check("git ls-files ran", False, str(e))

    print("=" * 60)
    if _failures == 0:
        print("\033[92mPASS\033[0m  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 6A Hermes Systemd Bundle)")
        print("Status: hermes systemd bundle completed (PASS)")
        return 0
    print(f"\033[91mFAIL\033[0m  {_failures} check(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())