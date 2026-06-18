#!/usr/bin/env python3
"""
validate_evomap_phase4b_isolated_capsule.py

Validates ATL-EVOMAP-4B Isolated Capsule Test.

Stdlib only. Strictly read-only. No network, no Hub, no secrets.

Checks (12):
  1. Phase 4B case report exists
  2. execution-trace-openclaw-tool-use.json exists and is valid JSON
  3. capsule-openclaw-tool-use-discipline-phase4b.json exists and is valid JSON
  4. capsule artifact contains: capsule_openclaw_tool_use_discipline_phase4b,
     gene_distilled_openclaw-tool-use-discipline-bare-compatible, execution_trace
  5. capsule-survival-check.txt exists and contains target_survived True
  6. isolation-capsule-setup-summary.json exists and is valid JSON
  7. evolver-run-isolated-capsule-output.txt exists
  8. evolver-review-isolated-capsule-output.txt exists
  9. data/cases.json phase contains ATL-EVOMAP-4B
 10. case README contains ATL-EVOMAP-4B
 11. secret scan PASS (no tokens / API keys / chat_ids in artifacts)
 12. git status: no root .evolver/ or memory/ tracked (per hard boundary)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase4b-isolated-capsule"
ARTIFACTS = CASE_DIR / "artifacts"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_4B_ISOLATED_CAPSULE_REPORT.md"
CASE_REPORT = CASE_DIR / "ATL_EVOMAP_4B_ISOLATED_CAPSULE_REPORT.md"
CASE_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

TARGET_CAPSULE_ID = "capsule_openclaw_tool_use_discipline_phase4b"
TARGET_GENE_ID = "gene_distilled_openclaw-tool-use-discipline-bare-compatible"

# Secret patterns (same convention as Phase 3C-V2 / 4A validators)
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
    print("ATL-EVOMAP-4B Isolated Capsule Test Validator")
    print("=" * 60)

    # 1. Case report exists
    _info("1. Checking Phase 4B case report exists...")
    _check("Phase 4B case report exists", CASE_REPORT.is_file())

    # 2. execution-trace-openclaw-tool-use.json exists and valid JSON
    _info("2. Checking execution-trace-openclaw-tool-use.json exists and is valid JSON...")
    trace_path = ARTIFACTS / "execution-trace-openclaw-tool-use.json"
    if not trace_path.is_file():
        _check("execution-trace-openclaw-tool-use.json exists", False)
    else:
        _check("execution-trace-openclaw-tool-use.json exists", True)
        try:
            trace_data = json.loads(trace_path.read_text())
            _check(
                "execution-trace is valid JSON with 'ok' field",
                "ok" in trace_data,
                f"ok={trace_data.get('ok')}",
            )
        except Exception as e:
            _check("execution-trace is valid JSON", False, str(e))

    # 3. capsule artifact exists and valid JSON
    _info("3. Checking capsule-openclaw-tool-use-discipline-phase4b.json exists and is valid JSON...")
    cap_path = ARTIFACTS / "capsule-openclaw-tool-use-discipline-phase4b.json"
    cap_data = None
    if not cap_path.is_file():
        _check("capsule artifact exists", False)
    else:
        _check("capsule artifact exists", True)
        try:
            cap_data = json.loads(cap_path.read_text())
            _check("capsule artifact is valid JSON", True)
        except Exception as e:
            _check("capsule artifact is valid JSON", False, str(e))

    # 4. capsule artifact contains required fields
    _info("4. Checking capsule artifact contains required fields...")
    if cap_data is not None:
        _check(
            "capsule.id == capsule_openclaw_tool_use_discipline_phase4b",
            cap_data.get("id") == TARGET_CAPSULE_ID,
            str(cap_data.get("id", "")),
        )
        gene_field = cap_data.get("gene") or cap_data.get("gene_id")
        _check(
            "capsule.gene == gene_distilled_openclaw-tool-use-discipline-bare-compatible",
            gene_field == TARGET_GENE_ID,
            str(gene_field),
        )
        trace = cap_data.get("execution_trace")
        _check(
            "capsule.execution_trace is non-empty list",
            isinstance(trace, list) and len(trace) > 0,
            f"type={type(trace).__name__}, len={len(trace) if isinstance(trace, list) else 0}",
        )
        # Verify execution_trace has at least one validate step
        if isinstance(trace, list):
            has_validate = any(t.get("stage") == "validate" for t in trace)
            _check(
                "execution_trace has at least one validate step",
                has_validate,
            )
    else:
        _check("capsule artifact content", False, "capsule artifact missing or invalid")

    # 5. capsule-survival-check.txt exists and contains target_survived True
    _info("5. Checking capsule-survival-check.txt exists and contains target_survived True...")
    surv_path = ARTIFACTS / "capsule-survival-check.txt"
    if not surv_path.is_file():
        _check("capsule-survival-check.txt exists", False)
    else:
        _check("capsule-survival-check.txt exists", True)
        text = surv_path.read_text()
        _check(
            "capsule-survival-check.txt contains 'target_survived True'",
            "target_survived True" in text,
        )
        _check(
            "capsule-survival-check.txt contains 'capsule_count 1'",
            "capsule_count 1" in text,
        )

    # 6. isolation-capsule-setup-summary.json exists and valid JSON
    _info("6. Checking isolation-capsule-setup-summary.json exists and is valid JSON...")
    summary_path = ARTIFACTS / "isolation-capsule-setup-summary.json"
    summary = None
    if not summary_path.is_file():
        _check("isolation-capsule-setup-summary.json exists", False)
    else:
        _check("isolation-capsule-setup-summary.json exists", True)
        try:
            summary = json.loads(summary_path.read_text())
            _check("isolation-capsule-setup-summary.json is valid JSON", True)
        except Exception as e:
            _check("isolation-capsule-setup-summary.json is valid JSON", False, str(e))

    # 7. evolver-run-isolated-capsule-output.txt exists
    _info("7. Checking evolver-run-isolated-capsule-output.txt exists...")
    _check(
        "evolver-run-isolated-capsule-output.txt exists",
        (ARTIFACTS / "evolver-run-isolated-capsule-output.txt").is_file(),
    )

    # 8. evolver-review-isolated-capsule-output.txt exists
    _info("8. Checking evolver-review-isolated-capsule-output.txt exists...")
    _check(
        "evolver-review-isolated-capsule-output.txt exists",
        (ARTIFACTS / "evolver-review-isolated-capsule-output.txt").is_file(),
    )

    # 9. data/cases.json phase contains ATL-EVOMAP-4B
    _info("9. Checking data/cases.json phase contains ATL-EVOMAP-4B...")
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
                # Phase 4B may have been superseded (e.g. by 4C), so accept
                # either current phase == 4B, or phase_history having 4B entry.
                current_phase = case.get("phase", "")
                hist = case.get("phase_history", [])
                phase_4b_hist = next(
                    (e for e in hist if e.get("phase") == "ATL-EVOMAP-4B"),
                    None,
                )
                _check(
                    "cases.json phase is ATL-EVOMAP-4B (current or historical)",
                    "ATL-EVOMAP-4B" in current_phase or phase_4b_hist is not None,
                    f"current={current_phase!r}, hist_entry={phase_4b_hist is not None}",
                )
                _check(
                    "cases.json status records 4B 'isolated capsule completed' (current or historical)",
                    "isolated capsule completed" in case.get("status", "")
                    or (phase_4b_hist is not None
                        and "isolated capsule completed" in phase_4b_hist.get("status", "")),
                    case.get("status", ""),
                )
                _check(
                    "cases.json phase_history has ATL-EVOMAP-4B entry",
                    phase_4b_hist is not None,
                )
        except Exception as e:
            _check("cases.json valid JSON", False, str(e))
    else:
        _check("data/cases.json exists", False)

    # 10. case README contains ATL-EVOMAP-4B
    _info("10. Checking case README contains ATL-EVOMAP-4B...")
    if CASE_README.is_file():
        text = CASE_README.read_text()
        _check("case README contains ATL-EVOMAP-4B", "ATL-EVOMAP-4B" in text)
    else:
        _check("case README exists", False)

    # 11. Secret scan
    _info("11. Scanning for secret patterns in Phase 4B artifacts...")
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
        _check("no secret patterns in Phase 4B artifacts", True)
    else:
        for p, pat in secret_hits:
            _check(f"no secret pattern '{pat}' in {p.name}", False)

    # 12. No root .evolver/ or memory/ tracked by git
    _info("12. Checking no root .evolver/ or memory/ tracked by git...")
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

    # Bonus: validate isolation-capsule-setup-summary.json content
    if summary is not None:
        _info("13. Validating isolation-capsule-setup-summary.json content...")
        _check("summary has isolated_runtime", "isolated_runtime" in summary)
        _check("summary has gene_count=1", summary.get("gene_count") == 1)
        _check(
            "summary.target_capsule_survived is true",
            summary.get("target_capsule_survived") is True,
        )
        _check(
            "summary.execution_trace_non_empty is true",
            summary.get("execution_trace_non_empty") is True,
        )
        _check("summary.hub is 'disabled'", summary.get("hub") == "disabled")
        _check("summary.publish is 'disabled'", summary.get("publish") == "disabled")
        _check("summary.credits is 0", summary.get("credits") == 0)
        _check("summary.approve is 'not_executed'", summary.get("approve") == "not_executed")
        _check("summary.solidify is 'not_executed'", summary.get("solidify") == "not_executed")
        _check(
            "summary.target_gene is bare-compatible",
            summary.get("target_gene") == TARGET_GENE_ID,
        )

    print("=" * 60)
    if _failures == 0:
        print("\033[92mPASS\033[0m  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 4B Isolated Capsule)")
        print("Status: isolated capsule completed (PASS)")
        return 0
    print(f"\033[91mFAIL\033[0m  {_failures} check(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
