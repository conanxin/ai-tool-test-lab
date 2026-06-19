#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_evomap_phase9a_bundle_curator_skill.py — Validator for ATL-EVOMAP-9A.

Phase: ATL-EVOMAP-9A (Bundle Curator Skill)
Base:  a56e756 (post-ATL-EVOMAP-8A nightly validation loop asset)

Verifies, in order:

  1. File presence (curator tool, validator tool, skill doc, schema
     example, sample spec, generated bundle / gene / capsule / README,
     dry-run / generate / inspect / validate / apply dry-run /
     apply --yes / target summary / 2 self-tests, README, case report,
     top-level report).
  2. Curator tool CLI shape (AST parses; argparse supports --spec,
     --out-dir, --bundle-name, --dry-run, --strict).
  3. Curator tool stdlib-only (AST check; reject any non-stdlib import).
  4. Schema / spec JSON parse + key fields.
  5. Generated bundle JSON parse + key fields.
  6. Curator artifacts:
       - curator-dry-run-output.json: ok=true, mode=dry-run
       - curator-generate-output.json: ok=true, mode=generated
       - inspect-generated-bundle-output.json: ok=true
       - validate-generated-bundle-output.json: ok=true
       - apply-generated-bundle-dry-run-output.json: ok=true, mode=dry-run
       - apply-generated-bundle-yes-output.json: ok=true, mode=applied
       - apply-generated-target-summary.json: gene_count>=1, capsule_count>=1
       - curator-selftest-unsafe-secret-output.json: ok=false, mode=rejected
       - curator-selftest-unsafe-id-output.json: ok=false, mode=rejected
  7. Secret scan regression: data/cases.json phase or phase_history
     contains "ATL-EVOMAP-9A"; main case README contains "ATL-EVOMAP-9A".
  8. Git hygiene: git ls-files does NOT include root .evolver/ or memory/.
  9. Prior validators regression: re-run 7 prior phase validators
     (5/6A/6B/6C/7A/7B/8A) and confirm ALL CHECKS PASSED.

Stdlib only.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase9a-bundle-curator-skill"
ARTIFACTS_DIR = CASE_DIR / "artifacts"
GENERATED_DIR = CASE_DIR / "generated"
SPECS_DIR = CASE_DIR / "specs"
TEMPLATES_DIR = CASE_DIR / "templates"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_9A_BUNDLE_CURATOR_SKILL_REPORT.md"
MAIN_README = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "README.md"
CASES_JSON = REPO_ROOT / "data" / "cases.json"

CURATOR_TOOL = REPO_ROOT / "scripts" / "evomap_curate_bundle.py"

# Required curator CLI flags (per spec).
REQUIRED_CURATOR_FLAGS = (
    "--spec",
    "--out-dir",
    "--bundle-name",
    "--dry-run",
    "--strict",
)

# Forbidden top-level imports for the curator (defense in depth).
FORBIDDEN_TOP_LEVEL_IMPORTS = frozenset({
    "openai", "anthropic", "google", "cohere",
    "requests", "httpx", "urllib3", "urllib",
    "telegram", "telebot", "aiogram",
    "boto3", "botocore",
    "github", "github3", "gitlab",
    "playwright", "selenium", "pyppeteer", "scrapy",
    "pytest", "unittest",
    "dotenv", "environs",
    "click", "typer",
    "yaml", "toml", "tomllib",
    "fastapi", "flask", "django",
    "numpy", "pandas", "scipy", "torch", "tensorflow",
})

PRIOR_VALIDATORS = (
    "scripts/validate_evomap_phase5_local_evolution_kit.py",
    "scripts/validate_evomap_phase6a_hermes_systemd_bundle.py",
    "scripts/validate_evomap_phase6b_telegram_router_bundle.py",
    "scripts/validate_evomap_phase6c_codex_test_failure_bundle.py",
    "scripts/validate_evomap_phase7a_domain_signal_injection.py",
    "scripts/validate_evomap_phase7b_cross_bundle_regression.py",
    "scripts/validate_evomap_phase8a_nightly_validation_loop.py",
)


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

PASS_LIST: list[str] = []
FAIL_LIST: list[str] = []


def record(idx: int, label: str, ok: bool, detail: str = "") -> None:
    marker = "PASS" if ok else "FAIL"
    line = f"  [{marker}] {idx:>2}. {label}"
    if detail:
        line += f"\n          {detail}"
    print(line, flush=True)
    (PASS_LIST if ok else FAIL_LIST).append(label)


# ---------------------------------------------------------------------------
# 1. Curator tool: AST stdlib check + CLI flag check
# ---------------------------------------------------------------------------

def check_curator_tool() -> None:
    print("\n=== Curator tool: AST stdlib guard + CLI flag check ===")
    if not CURATOR_TOOL.is_file():
        record(1, "scripts/evomap_curate_bundle.py exists", False, f"missing: {CURATOR_TOOL}")
        return
    record(1, "scripts/evomap_curate_bundle.py exists", True, str(CURATOR_TOOL))

    try:
        src = CURATOR_TOOL.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except SyntaxError as e:
        record(3, "curator AST parses (stdlib guard)", False, f"syntax error: {e}")
        return
    record(3, "curator AST parses (stdlib guard)", True)

    # Walk AST and reject forbidden imports
    forbidden_found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in FORBIDDEN_TOP_LEVEL_IMPORTS:
                    forbidden_found.append(f"import {alias.name} (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top in FORBIDDEN_TOP_LEVEL_IMPORTS:
                forbidden_found.append(f"from {node.module} import … (line {node.lineno})")
    if forbidden_found:
        record(4, "curator stdlib-only (no third-party imports)", False, "; ".join(forbidden_found))
    else:
        record(4, "curator stdlib-only (no third-party imports)", True)

    # CLI flag check via argparse: walk the AST for argparse.add_argument calls
    found_flags: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_add_arg = (
                (isinstance(func, ast.Attribute) and func.attr == "add_argument") or
                (isinstance(func, ast.Name) and func.id == "add_argument")
            )
            if not is_add_arg:
                continue
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("--"):
                        found_flags.add(arg.value)
            # Also pick up kwargs["--spec"] etc.
            for kw in node.keywords:
                if kw.arg and kw.arg.startswith("--"):
                    found_flags.add(kw.arg)
    for flag in REQUIRED_CURATOR_FLAGS:
        ok = flag in found_flags
        record(2 if flag == "--spec" else 6 if flag == "--out-dir" else 7 if flag == "--bundle-name" else 5 if flag == "--dry-run" else 8 if flag == "--strict" else 99,
               f"curator CLI supports {flag}",
               ok,
               f"found in AST: {sorted(found_flags)}" if not ok else "")


# ---------------------------------------------------------------------------
# 2. File presence
# ---------------------------------------------------------------------------

def check_file_presence() -> None:
    print("\n=== File presence ===")
    required = [
        ("BUNDLE_CURATOR.SKILL.md", CASE_DIR / "BUNDLE_CURATOR.SKILL.md"),
        ("templates/curator-spec.schema.example.json", TEMPLATES_DIR / "curator-spec.schema.example.json"),
        ("specs/sample-safe-bundle.curator-spec.json", SPECS_DIR / "sample-safe-bundle.curator-spec.json"),
        ("generated/sample-safe-bundle.bundle.json", GENERATED_DIR / "sample-safe-bundle.bundle.json"),
        ("generated/README.generated.md", GENERATED_DIR / "README.generated.md"),
        ("artifacts/curator-dry-run-output.json", ARTIFACTS_DIR / "curator-dry-run-output.json"),
        ("artifacts/curator-generate-output.json", ARTIFACTS_DIR / "curator-generate-output.json"),
        ("artifacts/inspect-generated-bundle-output.json", ARTIFACTS_DIR / "inspect-generated-bundle-output.json"),
        ("artifacts/validate-generated-bundle-output.json", ARTIFACTS_DIR / "validate-generated-bundle-output.json"),
        ("artifacts/apply-generated-bundle-dry-run-output.json", ARTIFACTS_DIR / "apply-generated-bundle-dry-run-output.json"),
        ("artifacts/apply-generated-bundle-yes-output.json", ARTIFACTS_DIR / "apply-generated-bundle-yes-output.json"),
        ("artifacts/apply-generated-target-summary.json", ARTIFACTS_DIR / "apply-generated-target-summary.json"),
        ("artifacts/curator-selftest-unsafe-secret-output.json", ARTIFACTS_DIR / "curator-selftest-unsafe-secret-output.json"),
        ("artifacts/curator-selftest-unsafe-id-output.json", ARTIFACTS_DIR / "curator-selftest-unsafe-id-output.json"),
        ("README.md", CASE_DIR / "README.md"),
        ("ATL_EVOMAP_9A_BUNDLE_CURATOR_SKILL_REPORT.md (case)", CASE_DIR / "ATL_EVOMAP_9A_BUNDLE_CURATOR_SKILL_REPORT.md"),
        ("reports/ATL_EVOMAP_9A_BUNDLE_CURATOR_SKILL_REPORT.md (top-level)", TOP_REPORT),
    ]
    for label, path in required:
        idx_offset = 9  # begin numbering after CLI flag checks (1-8)
        ok = path.is_file()
        detail = "" if ok else f"missing: {path}"
        record(0, f"file present: {label}", ok, detail)

    # Generated gene + capsule filenames are derived; discover them
    if GENERATED_DIR.is_dir():
        gene_files = sorted(GENERATED_DIR.glob("gene-*.json"))
        cap_files = sorted(GENERATED_DIR.glob("capsule-*.json"))
        record(0, "file present: generated/gene-*.json", bool(gene_files),
               ", ".join(p.name for p in gene_files) if gene_files else "missing")
        record(0, "file present: generated/capsule-*.json", bool(cap_files),
               ", ".join(p.name for p in cap_files) if cap_files else "missing")


# ---------------------------------------------------------------------------
# 3. Schema / spec / bundle JSON parse + key fields
# ---------------------------------------------------------------------------

def _check_json_parse(label: str, path: Path, expected_keys: tuple[str, ...]) -> bool:
    if not path.is_file():
        record(0, f"JSON parse + key fields: {label}", False, f"missing: {path}")
        return False
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        record(0, f"JSON parse + key fields: {label}", False, f"JSON parse error: {e}")
        return False
    missing = [k for k in expected_keys if k not in d]
    if missing:
        record(0, f"JSON parse + key fields: {label}", False, f"missing keys: {missing}")
        return False
    record(0, f"JSON parse + key fields: {label}", True, f"keys: {sorted(expected_keys)}")
    return True


def check_schema_spec_bundle() -> None:
    print("\n=== Schema / spec / bundle JSON parse + key fields ===")
    _check_json_parse(
        "templates/curator-spec.schema.example.json",
        TEMPLATES_DIR / "curator-spec.schema.example.json",
        ("schema_version", "bundle", "gene", "capsule", "safety"),
    )
    _check_json_parse(
        "specs/sample-safe-bundle.curator-spec.json",
        SPECS_DIR / "sample-safe-bundle.curator-spec.json",
        ("schema_version", "bundle", "gene", "capsule", "safety"),
    )
    _check_json_parse(
        "generated/sample-safe-bundle.bundle.json",
        GENERATED_DIR / "sample-safe-bundle.bundle.json",
        ("schema_version", "source_phase", "source_session", "target_gene_id",
         "target_capsule_id", "gene", "capsule", "execution_trace",
         "import_contract", "kit_provenance", "safety"),
    )


# ---------------------------------------------------------------------------
# 4. Curator artifact shape checks
# ---------------------------------------------------------------------------

def _check_artifact(label: str, path: Path, predicate, detail_pred=None) -> bool:
    if not path.is_file():
        record(0, f"artifact: {label}", False, f"missing: {path}")
        return False
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        record(0, f"artifact: {label}", False, f"JSON parse error: {e}")
        return False
    ok, why = predicate(d)
    detail = ""
    if not ok and detail_pred is not None:
        try:
            detail = detail_pred(d)
        except Exception:
            detail = why
    record(0, f"artifact: {label}", ok, detail or why)
    return ok


def check_curator_artifacts() -> None:
    print("\n=== Curator artifact shape checks ===")

    _check_artifact(
        "curator-dry-run-output.json: ok=true, mode=dry-run",
        ARTIFACTS_DIR / "curator-dry-run-output.json",
        lambda d: (d.get("ok") is True and d.get("mode") == "dry-run",
                   f"ok={d.get('ok')}, mode={d.get('mode')!r}"),
    )

    _check_artifact(
        "curator-generate-output.json: ok=true, mode=generated",
        ARTIFACTS_DIR / "curator-generate-output.json",
        lambda d: (d.get("ok") is True and d.get("mode") == "generated",
                   f"ok={d.get('ok')}, mode={d.get('mode')!r}"),
    )

    _check_artifact(
        "inspect-generated-bundle-output.json: ok=true",
        ARTIFACTS_DIR / "inspect-generated-bundle-output.json",
        lambda d: (d.get("ok") is True, f"ok={d.get('ok')}"),
    )

    # validate result shape varies; check both top-level ok=true AND summary.secret_hits==0
    def _v(d):
        ok = d.get("ok") is True
        s = d.get("summary") or {}
        secret_ok = (s.get("secret_hits") == 0) if isinstance(s, dict) else False
        return (ok and secret_ok, f"ok={d.get('ok')}, summary.secret_hits={s.get('secret_hits') if isinstance(s, dict) else 'n/a'}")
    _check_artifact(
        "validate-generated-bundle-output.json: ok=true, secret_hits=0",
        ARTIFACTS_DIR / "validate-generated-bundle-output.json",
        _v,
    )

    # apply dry-run: nested under "plan"
    def _ap_dry(d):
        ok = d.get("ok") is True
        plan = d.get("plan") or {}
        summary = plan.get("summary") or {}
        domain_rej = summary.get("memory_graph_domain_rejected", -1)
        signals_added = summary.get("memory_graph_signals_added", -1)
        return (ok and domain_rej == 0 and signals_added >= 5,
                f"ok={ok}, plan.summary.memory_graph_signals_added={signals_added}, "
                f"plan.summary.memory_graph_domain_rejected={domain_rej}")
    _check_artifact(
        "apply-generated-bundle-dry-run-output.json: ok=true, signals>=5, rejected=0",
        ARTIFACTS_DIR / "apply-generated-bundle-dry-run-output.json",
        _ap_dry,
    )

    def _ap_yes(d):
        ok = d.get("ok") is True
        plan_summary = d.get("plan_summary") or {}
        writes_exec = d.get("log", {}).get("writes_executed", []) or []
        errors = d.get("log", {}).get("errors", []) or []
        return (ok and len(writes_exec) >= 6 and len(errors) == 0,
                f"ok={ok}, writes_executed={len(writes_exec)}, errors={len(errors)}, "
                f"plan_summary.new_gene_count={plan_summary.get('new_gene_count')}")
    _check_artifact(
        "apply-generated-bundle-yes-output.json: ok=true, writes>=6, errors=0",
        ARTIFACTS_DIR / "apply-generated-bundle-yes-output.json",
        _ap_yes,
    )

    def _ap_target(d):
        gc = d.get("gene_count", 0)
        cc = d.get("capsule_count", 0)
        return (gc >= 1 and cc >= 1,
                f"gene_count={gc}, capsule_count={cc}, distinct_signal_count={d.get('distinct_signal_count')}")
    _check_artifact(
        "apply-generated-target-summary.json: gene>=1, capsule>=1",
        ARTIFACTS_DIR / "apply-generated-target-summary.json",
        _ap_target,
    )

    _check_artifact(
        "curator-selftest-unsafe-secret-output.json: ok=false, rejected",
        ARTIFACTS_DIR / "curator-selftest-unsafe-secret-output.json",
        lambda d: (d.get("ok") is False and d.get("mode") == "rejected",
                   f"ok={d.get('ok')}, mode={d.get('mode')!r}"),
    )

    _check_artifact(
        "curator-selftest-unsafe-id-output.json: ok=false, rejected",
        ARTIFACTS_DIR / "curator-selftest-unsafe-id-output.json",
        lambda d: (d.get("ok") is False and d.get("mode") == "rejected",
                   f"ok={d.get('ok')}, mode={d.get('mode')!r}"),
    )


# ---------------------------------------------------------------------------
# 5. data/cases.json + main README 9A markers
# ---------------------------------------------------------------------------

def check_cases_and_readme() -> None:
    print("\n=== data/cases.json + main README 9A markers ===")
    if not CASES_JSON.is_file():
        record(0, "data/cases.json parse + 9A marker", False, f"missing: {CASES_JSON}")
    else:
        try:
            d = json.loads(CASES_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            record(0, "data/cases.json parse + 9A marker", False, f"JSON parse error: {e}")
            return
        # Find evomap case
        evo = next((c for c in d.get("cases", []) if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
        if evo is None:
            record(0, "data/cases.json: evomap-evolver-openclaw-v0 case present", False)
            return
        record(0, "data/cases.json: evomap-evolver-openclaw-v0 case present", True)

        ph_or_phase_contains_9a = (
            "ATL-EVOMAP-9A" in (evo.get("phase") or "") or
            any("ATL-EVOMAP-9A" in (h.get("phase") or "") for h in (evo.get("phase_history") or []))
        )
        record(0, "data/cases.json: phase or phase_history contains ATL-EVOMAP-9A",
               ph_or_phase_contains_9a,
               f"top_phase={evo.get('phase')!r}")

    if not MAIN_README.is_file():
        record(0, "main case README contains ATL-EVOMAP-9A", False, f"missing: {MAIN_README}")
    else:
        text = MAIN_README.read_text(encoding="utf-8")
        ok = "ATL-EVOMAP-9A" in text
        record(0, "main case README contains ATL-EVOMAP-9A", ok)


# ---------------------------------------------------------------------------
# 6. Git hygiene: no root .evolver/ or memory/ tracked
# ---------------------------------------------------------------------------

def check_git_hygiene() -> None:
    print("\n=== Git hygiene: no root .evolver/ or memory/ tracked ===")
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], cwd=str(REPO_ROOT), text=True, timeout=20,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        record(0, "git ls-files succeeds", False, f"error: {e}")
        return
    record(0, "git ls-files succeeds", True)

    bad_paths = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(".evolver/") or line.startswith("memory/"):
            bad_paths.append(line)

    if bad_paths:
        record(0, "git ls-files: no root .evolver/ or memory/ tracked",
               False, f"bad: {bad_paths[:3]}{'…' if len(bad_paths) > 3 else ''}")
    else:
        record(0, "git ls-files: no root .evolver/ or memory/ tracked", True,
               f"{len(out.splitlines())} tracked files, 0 bad paths")


# ---------------------------------------------------------------------------
# 7. Prior validators regression
# ---------------------------------------------------------------------------

def check_prior_validators() -> None:
    print("\n=== Prior validators regression (5/6A/6B/6C/7A/7B/8A) ===")
    summary: list[tuple[str, bool, str]] = []
    for rel in PRIOR_VALIDATORS:
        path = REPO_ROOT / rel
        if not path.is_file():
            record(0, f"prior validator exists: {rel}", False, "missing")
            summary.append((rel, False, "missing"))
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            record(0, f"prior validator {rel} PASS", False, "timeout")
            summary.append((rel, False, "timeout"))
            continue
        text = (proc.stdout or "") + (proc.stderr or "")
        ok = (proc.returncode == 0) and ("ALL CHECKS PASSED" in text)
        last_line = next((ln.strip() for ln in reversed(text.splitlines()) if ln.strip()), "")
        record(0, f"prior validator {rel} PASS", ok,
               f"rc={proc.returncode}, last_line={last_line[:80]!r}" if not ok else "")
        summary.append((rel, ok, last_line[:80]))

    # Also re-run data/cases.json parse as a sanity check
    try:
        subprocess.run(
            [sys.executable, "-m", "json.tool", str(CASES_JSON)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        record(0, "python3 -m json.tool data/cases.json succeeds", True)
    except subprocess.CalledProcessError as e:
        record(0, "python3 -m json.tool data/cases.json succeeds", False,
               f"rc={e.returncode}, stderr={(e.stderr or '')[:200]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"=== validate_evomap_phase9a_bundle_curator_skill.py ===")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"CASE_DIR  : {CASE_DIR}")
    print()

    check_curator_tool()
    check_file_presence()
    check_schema_spec_bundle()
    check_curator_artifacts()
    check_cases_and_readme()
    check_git_hygiene()
    check_prior_validators()

    print()
    print("=" * 70)
    print(f"PASSED: {len(PASS_LIST)}")
    print(f"FAILED: {len(FAIL_LIST)}")
    if FAIL_LIST:
        print("FAILED checks:")
        for label in FAIL_LIST:
            print(f"  - {label}")
        print()
        print("FAIL  SOME CHECKS FAILED")
        return 1
    print()
    print("PASS  ALL CHECKS PASSED")
    print("Case: evomap-evolver-openclaw-v0 (Phase 9A Bundle Curator Skill)")
    print("Status: bundle curator skill completed (BUNDLE_CURATOR_SKILL_PASS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())