#!/usr/bin/env python3
"""
validate_evomap_phase5_local_evolution_kit.py

Validates ATL-EVOMAP-5 Local Evolution Kit.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.

Checks (17):
  1. Phase 5 README exists
  2. Phase 5 case report exists
  3. bundle/openclaw-tool-use-discipline.bundle.json exists and is valid JSON
  4. scripts/evomap_inspect_bundle.py exists
  5. scripts/evomap_validate_bundle.py exists
  6. scripts/evomap_apply_bundle.py exists
  7. case tools/ has 3 script copies
  8. templates has 3 files (GENE / CAPSULE / MEMORY_GRAPH_SIGNAL)
  9. artifacts/inspect-bundle-output.json exists and ok=true
 10. artifacts/validate-bundle-output.json exists and ok=true
 11. artifacts/apply-bundle-dry-run-output.json exists
 12. artifacts/apply-bundle-yes-output.json exists
 13. artifacts/apply-target-summary.json exists with gene_count >= 1, capsule_count >= 1, memory_graph_lines >= 5
 14. data/cases.json phase contains ATL-EVOMAP-5
 15. case README contains ATL-EVOMAP-5
 16. secret scan PASS
 17. git status: no root .evolver/ or memory/ tracked
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase5-local-evolution-kit"
KIT_ARTIFACTS = KIT_DIR / "artifacts"
KIT_BUNDLE = KIT_DIR / "bundle" / "openclaw-tool-use-discipline.bundle.json"
KIT_TOOLS = KIT_DIR / "tools"
KIT_TEMPLATES = KIT_DIR / "templates"
KIT_README = KIT_DIR / "README.md"
KIT_REPORT = KIT_DIR / "ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_5_LOCAL_EVOLUTION_KIT_REPORT.md"
CASE_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

TOP_TOOLS = REPO_ROOT / "scripts"

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
    print("ATL-EVOMAP-5 Local Evolution Kit Validator")
    print("=" * 60)

    # 1. Phase 5 README exists
    _info("1. Checking Phase 5 README exists...")
    _check("Phase 5 README exists", KIT_README.is_file())

    # 2. Phase 5 case report exists
    _info("2. Checking Phase 5 case report exists...")
    _check("Phase 5 case report exists", KIT_REPORT.is_file())

    # 3. bundle exists and valid JSON
    _info("3. Checking bundle/openclaw-tool-use-discipline.bundle.json exists and is valid JSON...")
    bundle = None
    if not KIT_BUNDLE.is_file():
        _check("canonical bundle exists", False)
    else:
        _check("canonical bundle exists", True)
        try:
            bundle = json.loads(KIT_BUNDLE.read_text())
            _check("canonical bundle is valid JSON", True)
        except Exception as e:
            _check("canonical bundle is valid JSON", False, str(e))
    if bundle is not None:
        _check("bundle has 'gene' field", "gene" in bundle)
        _check("bundle has 'capsule' field", "capsule" in bundle)
        _check("bundle has 'execution_trace' field", "execution_trace" in bundle)
        _check("bundle has 'safety' field", "safety" in bundle)
        _check("bundle has 'import_contract' field", "import_contract" in bundle)
        # Check that safety has all required fields per spec
        if "safety" in bundle:
            safety = bundle["safety"]
            for k in ["hub", "publish", "credits", "visibility", "no_failed_events", "no_pollution_signals"]:
                _check(f"safety.{k} present", k in safety)

    # 4-6. Top-level tool scripts exist
    _info("4-6. Checking top-level scripts/ tool scripts exist...")
    for tool in ["evomap_inspect_bundle.py", "evomap_validate_bundle.py", "evomap_apply_bundle.py"]:
        _check(f"scripts/{tool} exists", (TOP_TOOLS / tool).is_file())

    # 7. Case tools/ has 3 script copies
    _info("7. Checking case tools/ has 3 script copies...")
    for tool in ["evomap_inspect_bundle.py", "evomap_validate_bundle.py", "evomap_apply_bundle.py"]:
        _check(f"case tools/{tool} exists", (KIT_TOOLS / tool).is_file())

    # 8. templates has 3 files
    _info("8. Checking templates/ has 3 template files...")
    for tmpl in ["GENE_TEMPLATE.json", "CAPSULE_TEMPLATE.json", "MEMORY_GRAPH_SIGNAL_TEMPLATE.jsonl"]:
        _check(f"templates/{tmpl} exists", (KIT_TEMPLATES / tmpl).is_file())

    # 9. inspect-bundle-output.json exists and ok=true
    _info("9. Checking inspect-bundle-output.json exists and ok=true...")
    inspect_out = KIT_ARTIFACTS / "inspect-bundle-output.json"
    if inspect_out.is_file():
        try:
            d = json.loads(inspect_out.read_text())
            _check("inspect-bundle-output.json ok=true", d.get("ok") is True)
        except Exception as e:
            _check("inspect-bundle-output.json valid JSON", False, str(e))
    else:
        _check("inspect-bundle-output.json exists", False)

    # 10. validate-bundle-output.json exists and ok=true
    _info("10. Checking validate-bundle-output.json exists and ok=true...")
    validate_out = KIT_ARTIFACTS / "validate-bundle-output.json"
    if validate_out.is_file():
        try:
            d = json.loads(validate_out.read_text())
            _check("validate-bundle-output.json ok=true", d.get("ok") is True)
            n_checks = len(d.get("checks", []))
            n_pass = sum(1 for c in d.get("checks", []) if c.get("ok"))
            _check(f"validate-bundle-output.json has 12+ checks", n_checks >= 12, f"{n_pass}/{n_checks} pass")
        except Exception as e:
            _check("validate-bundle-output.json valid JSON", False, str(e))
    else:
        _check("validate-bundle-output.json exists", False)

    # 11. apply-bundle-dry-run-output.json exists
    _info("11. Checking apply-bundle-dry-run-output.json exists...")
    dry_run_out = KIT_ARTIFACTS / "apply-bundle-dry-run-output.json"
    if dry_run_out.is_file():
        try:
            d = json.loads(dry_run_out.read_text())
            _check("apply-dry-run mode='dry-run'", d.get("mode") == "dry-run")
        except Exception as e:
            _check("apply-dry-run valid JSON", False, str(e))
    else:
        _check("apply-bundle-dry-run-output.json exists", False)

    # 12. apply-bundle-yes-output.json exists
    _info("12. Checking apply-bundle-yes-output.json exists...")
    yes_out = KIT_ARTIFACTS / "apply-bundle-yes-output.json"
    if yes_out.is_file():
        try:
            d = json.loads(yes_out.read_text())
            _check("apply-yes mode='applied'", d.get("mode") == "applied")
            _check("apply-yes ok=true", d.get("ok") is True)
        except Exception as e:
            _check("apply-yes valid JSON", False, str(e))
    else:
        _check("apply-bundle-yes-output.json exists", False)

    # 13. apply-target-summary.json exists with valid counts
    _info("13. Checking apply-target-summary.json has valid counts...")
    summary_out = KIT_ARTIFACTS / "apply-target-summary.json"
    if summary_out.is_file():
        try:
            d = json.loads(summary_out.read_text())
            _check("summary.gene_count >= 1", d.get("gene_count", 0) >= 1, str(d.get("gene_count")))
            _check("summary.capsule_count >= 1", d.get("capsule_count", 0) >= 1, str(d.get("capsule_count")))
            _check("summary.memory_graph_lines >= 5", d.get("memory_graph_lines", 0) >= 5, str(d.get("memory_graph_lines")))
        except Exception as e:
            _check("apply-target-summary.json valid JSON", False, str(e))
    else:
        _check("apply-target-summary.json exists", False)

    # 14. data/cases.json phase contains ATL-EVOMAP-5
    _info("14. Checking data/cases.json phase contains ATL-EVOMAP-5...")
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
                _check(
                    "cases.json phase contains ATL-EVOMAP-5",
                    "ATL-EVOMAP-5" in case.get("phase", ""),
                    case.get("phase", ""),
                )
                _check(
                    "cases.json status contains 'local evolution kit completed'",
                    "local evolution kit completed" in case.get("status", ""),
                    case.get("status", ""),
                )
                hist = case.get("phase_history", [])
                has_5 = any(e.get("phase") == "ATL-EVOMAP-5" for e in hist)
                _check("cases.json phase_history has ATL-EVOMAP-5 entry", has_5)
        except Exception as e:
            _check("cases.json valid JSON", False, str(e))
    else:
        _check("data/cases.json exists", False)

    # 15. case README contains ATL-EVOMAP-5
    _info("15. Checking case README contains ATL-EVOMAP-5...")
    if CASE_README.is_file():
        text = CASE_README.read_text()
        _check("case README contains ATL-EVOMAP-5", "ATL-EVOMAP-5" in text)
    else:
        _check("case README exists", False)

    # 16. Secret scan
    _info("16. Scanning for secret patterns in Phase 5 artifacts...")
    scan_paths = [
        KIT_ARTIFACTS, KIT_BUNDLE, KIT_README, KIT_REPORT, TOP_REPORT, CASE_README, CASES_JSON,
        KIT_TOOLS, KIT_TEMPLATES,
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
        _check("no secret patterns in Phase 5 artifacts", True)
    else:
        for p, pat in secret_hits:
            _check(f"no secret pattern '{pat}' in {p.name}", False)

    # 17. No root .evolver/ or memory/ tracked by git
    _info("17. Checking no root .evolver/ or memory/ tracked by git...")
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
        print("Case: evomap-evolver-openclaw-v0 (Phase 5 Local Evolution Kit)")
        print("Status: local evolution kit completed (PASS)")
        return 0
    print(f"\033[91mFAIL\033[0m  {_failures} check(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
