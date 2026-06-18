#!/usr/bin/env python3
"""
validate_evomap_phase4c_cross_session_reuse.py

Validates ATL-EVOMAP-4C Cross-Session Reuse Test.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.

Checks (14):
  1. Phase 4C case report exists
  2. portable-openclaw-gene-capsule-bundle.json exists and is valid JSON
  3. bundle contains gene, capsule, execution_trace
  4. capsule-survival-session-a.txt exists and contains found_target True
  5. capsule-survival-session-b.txt exists and contains found_target True
  6. cross-session-setup-summary.json exists and is valid JSON
  7. evolver-run-session-a-output.txt exists
  8. evolver-run-session-b-output.txt exists
  9. evolver-review-session-a-output.txt exists
 10. evolver-review-session-b-output.txt exists
 11. data/cases.json phase contains ATL-EVOMAP-4C
 12. case README contains ATL-EVOMAP-4C
 13. secret scan PASS
 14. git status: no root .evolver/ or memory/ tracked
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase4c-cross-session-reuse"
ARTIFACTS = CASE_DIR / "artifacts"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_4C_CROSS_SESSION_REUSE_REPORT.md"
CASE_REPORT = CASE_DIR / "ATL_EVOMAP_4C_CROSS_SESSION_REUSE_REPORT.md"
CASE_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

TARGET_CAPSULE_ID = "capsule_openclaw_tool_use_discipline_phase4b"
TARGET_GENE_ID = "gene_distilled_openclaw-tool-use-discipline-bare-compatible"

# Secret patterns
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
    print("ATL-EVOMAP-4C Cross-Session Reuse Test Validator")
    print("=" * 60)

    # 1. Phase 4C case report exists
    _info("1. Checking Phase 4C case report exists...")
    _check("Phase 4C case report exists", CASE_REPORT.is_file())

    # 2. portable bundle exists and valid JSON
    _info("2. Checking portable-openclaw-gene-capsule-bundle.json exists and is valid JSON...")
    bundle_path = ARTIFACTS / "portable-openclaw-gene-capsule-bundle.json"
    bundle = None
    if not bundle_path.is_file():
        _check("portable bundle exists", False)
    else:
        _check("portable bundle exists", True)
        try:
            bundle = json.loads(bundle_path.read_text())
            _check("portable bundle is valid JSON", True)
        except Exception as e:
            _check("portable bundle is valid JSON", False, str(e))

    # 3. bundle contains gene, capsule, execution_trace
    _info("3. Checking portable bundle contains gene, capsule, execution_trace...")
    if bundle is not None:
        _check("bundle has 'gene' field", "gene" in bundle)
        _check("bundle has 'capsule' field", "capsule" in bundle)
        _check("bundle has 'execution_trace' field", "execution_trace" in bundle)
        # Verify ids match
        gene = bundle.get("gene", {})
        capsule = bundle.get("capsule", {})
        _check(
            "bundle.gene.id == gene_distilled_openclaw-tool-use-discipline-bare-compatible",
            gene.get("id") == TARGET_GENE_ID,
            str(gene.get("id", "")),
        )
        _check(
            "bundle.capsule.id == capsule_openclaw_tool_use_discipline_phase4b",
            capsule.get("id") == TARGET_CAPSULE_ID,
            str(capsule.get("id", "")),
        )
        # Check bundle has import_contract
        _check("bundle has 'import_contract'", "import_contract" in bundle)
        # Check required files
        if "import_contract" in bundle:
            req = bundle["import_contract"].get("required_files", [])
            _check(
                "import_contract has 3 required files",
                len(req) == 3,
                f"count={len(req)}",
            )
    else:
        _check("bundle contents", False, "bundle missing or invalid")

    # 4. capsule-survival-session-a.txt exists and contains found_target True
    _info("4. Checking capsule-survival-session-a.txt contains found_target True...")
    surv_a = ARTIFACTS / "capsule-survival-session-a.txt"
    if not surv_a.is_file():
        _check("capsule-survival-session-a.txt exists", False)
    else:
        _check("capsule-survival-session-a.txt exists", True)
        text_a = surv_a.read_text()
        _check("capsule-survival-session-a.txt contains 'found_target True'", "found_target True" in text_a)
        _check("capsule-survival-session-a.txt contains 'capsule_count 1'", "capsule_count 1" in text_a)
        _check("capsule-survival-session-a.txt has execution_trace_steps 4", "execution_trace_steps 4" in text_a)

    # 5. capsule-survival-session-b.txt exists and contains found_target True
    _info("5. Checking capsule-survival-session-b.txt contains found_target True...")
    surv_b = ARTIFACTS / "capsule-survival-session-b.txt"
    if not surv_b.is_file():
        _check("capsule-survival-session-b.txt exists", False)
    else:
        _check("capsule-survival-session-b.txt exists", True)
        text_b = surv_b.read_text()
        _check("capsule-survival-session-b.txt contains 'found_target True'", "found_target True" in text_b)
        _check("capsule-survival-session-b.txt contains 'capsule_count 1'", "capsule_count 1" in text_b)
        _check("capsule-survival-session-b.txt has execution_trace_steps 4", "execution_trace_steps 4" in text_b)

    # 6. cross-session-setup-summary.json exists and valid JSON
    _info("6. Checking cross-session-setup-summary.json exists and is valid JSON...")
    summary_path = ARTIFACTS / "cross-session-setup-summary.json"
    summary = None
    if not summary_path.is_file():
        _check("cross-session-setup-summary.json exists", False)
    else:
        _check("cross-session-setup-summary.json exists", True)
        try:
            summary = json.loads(summary_path.read_text())
            _check("cross-session-setup-summary.json is valid JSON", True)
        except Exception as e:
            _check("cross-session-setup-summary.json is valid JSON", False, str(e))

    # 7-10. evolver output files exist
    _info("7-10. Checking 4 evolver output files exist...")
    out_files = [
        "evolver-run-session-a-output.txt",
        "evolver-run-session-b-output.txt",
        "evolver-review-session-a-output.txt",
        "evolver-review-session-b-output.txt",
    ]
    for fname in out_files:
        _check(f"{fname} exists", (ARTIFACTS / fname).is_file())

    # 11. data/cases.json phase contains ATL-EVOMAP-4C
    _info("11. Checking data/cases.json phase contains ATL-EVOMAP-4C...")
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
                # Phase 4C may have been superseded (e.g. by 5), so accept
                # either current phase == 4C, or phase_history having 4C entry.
                current_phase = case.get("phase", "")
                hist = case.get("phase_history", [])
                phase_4c_hist = next(
                    (e for e in hist if e.get("phase") == "ATL-EVOMAP-4C"),
                    None,
                )
                _check(
                    "cases.json phase is ATL-EVOMAP-4C (current or historical)",
                    "ATL-EVOMAP-4C" in current_phase or phase_4c_hist is not None,
                    f"current={current_phase!r}, hist_entry={phase_4c_hist is not None}",
                )
                _check(
                    "cases.json status records 4C 'cross-session reuse completed' (current or historical)",
                    "cross-session reuse completed" in case.get("status", "")
                    or (phase_4c_hist is not None
                        and "cross-session reuse completed" in phase_4c_hist.get("status", "")),
                    case.get("status", ""),
                )
                _check(
                    "cases.json phase_history has ATL-EVOMAP-4C entry",
                    phase_4c_hist is not None,
                )
        except Exception as e:
            _check("cases.json valid JSON", False, str(e))
    else:
        _check("data/cases.json exists", False)

    # 12. case README contains ATL-EVOMAP-4C
    _info("12. Checking case README contains ATL-EVOMAP-4C...")
    if CASE_README.is_file():
        text = CASE_README.read_text()
        _check("case README contains ATL-EVOMAP-4C", "ATL-EVOMAP-4C" in text)
    else:
        _check("case README exists", False)

    # 13. Secret scan
    _info("13. Scanning for secret patterns in Phase 4C artifacts...")
    scan_paths = [ARTIFACTS, CASE_REPORT, TOP_REPORT, CASE_README, CASES_JSON]
    secret_hits = []
    for path in scan_paths:
        if not path.is_file():
            continue
        if path.is_dir():
            for p in path.rglob("*"):
                if p.is_file() and p.suffix in {".txt", ".json", ".md"}:
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
        _check("no secret patterns in Phase 4C artifacts", True)
    else:
        for p, pat in secret_hits:
            _check(f"no secret pattern '{pat}' in {p.name}", False)

    # 14. No root .evolver/ or memory/ tracked by git
    _info("14. Checking no root .evolver/ or memory/ tracked by git...")
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

    # Bonus: validate cross-session-setup-summary.json content
    if summary is not None:
        _info("15. Validating cross-session-setup-summary.json content...")
        _check("summary.session_a present", "session_a" in summary)
        _check("summary.session_b present", "session_b" in summary)
        _check("summary.gene_id == bare-compatible", summary.get("gene_id") == TARGET_GENE_ID)
        _check("summary.capsule_id == phase4b", summary.get("capsule_id") == TARGET_CAPSULE_ID)
        _check("summary.gene_imported_session_a", summary.get("gene_imported_session_a") is True)
        _check("summary.gene_imported_session_b", summary.get("gene_imported_session_b") is True)
        _check("summary.capsule_imported_session_a", summary.get("capsule_imported_session_a") is True)
        _check("summary.capsule_imported_session_b", summary.get("capsule_imported_session_b") is True)
        _check("summary.capsule_survived_session_a", summary.get("capsule_survived_session_a") is True)
        _check("summary.capsule_survived_session_b", summary.get("capsule_survived_session_b") is True)
        _check("summary.selector_hit_openclaw_gene_session_a", summary.get("selector_hit_openclaw_gene_session_a") is True)
        _check("summary.selector_hit_openclaw_gene_session_b", summary.get("selector_hit_openclaw_gene_session_b") is True)
        _check("summary.capsule_trigger_match_session_a", summary.get("capsule_trigger_match_session_a") is True)
        _check("summary.capsule_trigger_match_session_b", summary.get("capsule_trigger_match_session_b") is True)
        _check("summary.hub == 'disabled'", summary.get("hub") == "disabled")
        _check("summary.publish == 'disabled'", summary.get("publish") == "disabled")
        _check("summary.credits == 0", summary.get("credits") == 0)
        _check("summary.approve == 'not_executed'", summary.get("approve") == "not_executed")
        _check("summary.solidify == 'not_executed'", summary.get("solidify") == "not_executed")
        _check("summary.pollution_events == false", summary.get("pollution_events") is False)

    # Bonus: cross-session consistency check (A == B for capsule identity)
    if surv_a.is_file() and surv_b.is_file():
        _info("16. Cross-session consistency (A == B)...")
        a_lines = [l for l in surv_a.read_text().splitlines() if l.startswith(("capsule_count", "gene", "status", "confidence", "execution_trace_non_empty", "execution_trace_steps"))]
        b_lines = [l for l in surv_b.read_text().splitlines() if l.startswith(("capsule_count", "gene", "status", "confidence", "execution_trace_non_empty", "execution_trace_steps"))]
        _check("Session A and B survival output identical", a_lines == b_lines)

    print("=" * 60)
    if _failures == 0:
        print("\033[92mPASS\033[0m  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 4C Cross-Session Reuse)")
        print("Status: cross-session reuse completed (PASS)")
        return 0
    print(f"\033[91mFAIL\033[0m  {_failures} check(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
