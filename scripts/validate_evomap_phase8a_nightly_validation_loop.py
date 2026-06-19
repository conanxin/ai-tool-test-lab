#!/usr/bin/env python3
"""
validate_evomap_phase8a_nightly_validation_loop.py — Phase 8A Validator (22 checks)

Forwards-compatible: accepts ATL-EVOMAP-5/6A/6B/6C/7A/7B/8A entries in
phase_history so this validator stays green as the case progresses.

Hard rules (enforced by tool design):
- Python stdlib only (argparse, json, re, sys, pathlib, subprocess, ast)
- Runs in current working directory (the ai-tool-test-lab repo root)
- Does NOT contact Hub, does NOT publish, does NOT consume credits
- Does NOT execute evolver --approve or evolver solidify
- Does NOT commit runtime .evolver/ or memory/ originals
- Pure file-level + JSON-level + AST-level checks; no network calls; no shell
  exec for curl/wget/HTTP

Checks (22):
 1.  scripts/evomap_nightly_validate.py exists
 2.  nightly runner source is Python stdlib only (AST import scan)
 3.  nightly runner declares --repo-root argparse flag
 4.  nightly runner declares --out-dir argparse flag
 5.  nightly runner declares --markdown-name and --json-name argparse flags
 6.  nightly runner declares --output-dir backward-compat alias for --out-dir
 7.  nightly runner declares all 22 hard-boundary flags in digest output
 8.  validation-loop-manifest.json exists
 9.  validation-loop-manifest.json parses as valid JSON
10.  manifest has schema_version = "atl-evomap-nightly-validation-v0.1"
11.  manifest has source_base_commit
12.  manifest declares all 6 prior phase validators in `validators` list
13.  manifest declares all 4 canonical bundles in `bundles` list
14.  manifest runner.stdlib_only == true
15.  manifest cron_integration.installed == false and example_path contains cron.example
16.  templates/cron.example exists, is dry-run only, not a real drop-in
17.  nightly digest JSON exists at the spec'd default filename
18.  digest JSON overall_status == PASS
19.  digest JSON has 9 blocking checks passed (9/9)
20.  digest Markdown exists at the spec'd default filename
21.  data/cases.json phase or phase_history contains ATL-EVOMAP-8A
22.  prior validators (5, 6A, 6B, 6C, 7A, 7B) ALL CHECKS PASSED
     AND nightly runner itself exits 0 (backward-compat + self-host)
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# Repo root (cwd). All paths are relative to this.
REPO = Path.cwd()

CASE_DIR = REPO / "cases" / "evomap-evolver-openclaw-v0" / "phase8a-nightly-validation-loop"
ART_DIR = CASE_DIR / "artifacts"
TEMPLATES_DIR = CASE_DIR / "templates"

RUNNER = REPO / "scripts" / "evomap_nightly_validate.py"
MANIFEST = CASE_DIR / "validation-loop-manifest.json"
CRON_EXAMPLE = TEMPLATES_DIR / "cron.example"

# Per spec: default output filenames
DIGEST_JSON = ART_DIR / "nightly-validation-digest.json"
DIGEST_MD = ART_DIR / "nightly-validation-digest.md"
RUN_LOG = ART_DIR / "nightly-validation-run.log"

DATA_CASES = REPO / "data" / "cases.json"
MAIN_CASE_README = REPO / "cases" / "evomap-evolver-openclaw-v0" / "README.md"

# Python stdlib top-level modules (used for AST import guard)
STDLIB_TOP_LEVEL = {
    "__future__", "argparse", "ast", "collections", "contextlib", "csv",
    "dataclasses", "datetime", "functools", "hashlib", "hmac", "io",
    "itertools", "json", "mimetypes", "os", "pathlib", "re", "secrets",
    "shutil", "signal", "socket", "sqlite3", "stat", "string", "struct",
    "subprocess", "sys", "tempfile", "textwrap", "threading", "time",
    "traceback", "typing", "unicodedata", "unittest", "urllib", "uuid",
    "warnings", "weakref", "zipfile", "zlib",
}


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def _stdlib_only_check(path: Path) -> tuple[bool, str]:
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"cannot read source: {exc}"
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        return False, f"syntax error: {exc}"
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                top = n.name.split(".")[0]
                if top not in STDLIB_TOP_LEVEL:
                    bad.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".")[0]
            if top not in STDLIB_TOP_LEVEL:
                bad.append(node.module)
    if bad:
        return False, "non-stdlib imports: " + ", ".join(sorted(set(bad)))
    return True, "stdlib-only verified"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validator for ATL-EVOMAP-8A Nightly Validation Loop Asset."
    )
    parser.add_argument("--strict", action="store_true",
                        help="(no-op) this validator is strict by default")
    args = parser.parse_args()

    results: list[dict] = []

    # 1. nightly runner exists
    results.append(_check(
        "1. scripts/evomap_nightly_validate.py exists",
        RUNNER.exists(),
        str(RUNNER.relative_to(REPO)) if RUNNER.exists() else "missing",
    ))

    # 2. nightly runner source is Python stdlib only
    if RUNNER.exists():
        ok, detail = _stdlib_only_check(RUNNER)
        results.append(_check(
            "2. nightly runner source is Python stdlib only (AST import scan)",
            ok, detail,
        ))
    else:
        results.append(_check(
            "2. nightly runner source is Python stdlib only (AST import scan)",
            False, "runner missing",
        ))

    # 3-6. CLI flag checks
    if RUNNER.exists():
        src = RUNNER.read_text(encoding="utf-8")
        # 3. --repo-root
        has_repo_root = "--repo-root" in src and "repo_root" in src
        results.append(_check(
            "3. nightly runner declares --repo-root argparse flag",
            has_repo_root,
            "found --repo-root + repo_root reference"
            if has_repo_root else "missing --repo-root flag",
        ))
        # 4. --out-dir
        has_out_dir = "--out-dir" in src and "out_dir" in src
        results.append(_check(
            "4. nightly runner declares --out-dir argparse flag",
            has_out_dir,
            "found --out-dir + out_dir reference"
            if has_out_dir else "missing --out-dir flag",
        ))
        # 5. --markdown-name and --json-name
        has_md_name = "--markdown-name" in src and "markdown_name" in src
        has_json_name = "--json-name" in src and "json_name" in src
        results.append(_check(
            "5. nightly runner declares --markdown-name and --json-name argparse flags",
            has_md_name and has_json_name,
            f"markdown_name={has_md_name}, json_name={has_json_name}",
        ))
        # 6. --output-dir backward-compat alias
        has_output_dir = "--output-dir" in src and "output_dir" in src
        results.append(_check(
            "6. nightly runner declares --output-dir backward-compat alias for --out-dir",
            has_output_dir,
            "found --output-dir + output_dir reference (backward-compat alias)"
            if has_output_dir else "missing --output-dir alias",
        ))
        # 7. 22 hard-boundary flags in digest
        required_boundaries = [
            "no_hub_connection", "no_a2a_hub_url", "no_evolver_loop",
            "no_evolver_run", "no_evolver_review",
            "no_evolver_review_approve", "no_evolver_solidify",
            "no_auto_publish", "no_credit_consumption", "no_atp_autobuy",
            "no_real_credentials_read", "no_env_file_content_scanned",
            "no_curl_or_http_calls", "no_telegram_api",
            "no_online_coding_apis", "no_real_test_runners",
            "no_real_cron_install", "no_crontab_write",
            "no_systemd_timer_create", "no_evolver_package_source_modify",
            "no_runtime_evolver_or_memory_tracked", "stdlib_only",
        ]
        missing = [b for b in required_boundaries if b not in src]
        results.append(_check(
            "7. nightly runner declares all 22 hard-boundary flags in digest",
            not missing,
            f"declared={len(required_boundaries) - len(missing)}/{len(required_boundaries)}"
            + (f"; missing={missing}" if missing else ""),
        ))
    else:
        for i in range(3, 8):
            results.append(_check(
                f"{i}. (runner missing — CLI/boundary checks skipped)",
                False, "runner missing",
            ))

    # 8. manifest exists
    results.append(_check(
        "8. validation-loop-manifest.json exists",
        MANIFEST.exists(),
        str(MANIFEST.relative_to(REPO)) if MANIFEST.exists() else "missing",
    ))

    # 9. manifest parses
    manifest: dict = {}
    if MANIFEST.exists():
        manifest = _read_json(MANIFEST)
        ok = isinstance(manifest, dict) and "__error__" not in manifest
        results.append(_check(
            "9. validation-loop-manifest.json parses as valid JSON",
            ok,
            "valid JSON object" if ok
            else f"parse error: {manifest.get('__error__', '?')}",
        ))
    else:
        results.append(_check(
            "9. validation-loop-manifest.json parses as valid JSON",
            False, "manifest missing",
        ))

    # 10. manifest schema_version
    schema_ok = (isinstance(manifest, dict) and
                 manifest.get("schema_version")
                 == "atl-evomap-nightly-validation-v0.1")
    results.append(_check(
        "10. manifest schema_version == 'atl-evomap-nightly-validation-v0.1'",
        schema_ok,
        f"schema_version={manifest.get('schema_version', '?')!r}"
        if isinstance(manifest, dict) else "manifest invalid",
    ))

    # 11. manifest source_base_commit
    sbc_ok = (isinstance(manifest, dict) and
              isinstance(manifest.get("source_base_commit"), str)
              and len(manifest.get("source_base_commit", "")) >= 7)
    results.append(_check(
        "11. manifest has source_base_commit (string, length >= 7)",
        sbc_ok,
        f"source_base_commit={manifest.get('source_base_commit', '?')!r}"
        if isinstance(manifest, dict) else "manifest invalid",
    ))

    # 12. manifest declares all 6 prior phase validators
    expected_validators = {
        "scripts/validate_evomap_phase5_local_evolution_kit.py",
        "scripts/validate_evomap_phase6a_hermes_systemd_bundle.py",
        "scripts/validate_evomap_phase6b_telegram_router_bundle.py",
        "scripts/validate_evomap_phase6c_codex_test_failure_bundle.py",
        "scripts/validate_evomap_phase7a_domain_signal_injection.py",
        "scripts/validate_evomap_phase7b_cross_bundle_regression.py",
    }
    declared_validators: set[str] = set()
    if isinstance(manifest, dict) and manifest:
        for v in manifest.get("validators", []) or []:
            if isinstance(v, str):
                declared_validators.add(v)
    missing_v = expected_validators - declared_validators
    results.append(_check(
        "12. manifest `validators` list contains all 6 prior phase validators",
        not missing_v,
        f"declared={len(declared_validators)}/{len(expected_validators)}"
        + (f"; missing={sorted(missing_v)}" if missing_v else ""),
    ))

    # 13. manifest declares all 4 canonical bundles
    expected_bundles = {
        "cases/evomap-evolver-openclaw-v0/phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json",
        "cases/evomap-evolver-openclaw-v0/phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json",
        "cases/evomap-evolver-openclaw-v0/phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json",
        "cases/evomap-evolver-openclaw-v0/phase6c-codex-test-failure-bundle/bundle/codex-test-failure-loop.bundle.json",
    }
    declared_bundles: set[str] = set()
    if isinstance(manifest, dict) and manifest:
        for b in manifest.get("bundles", []) or []:
            if isinstance(b, str):
                declared_bundles.add(b)
    missing_b = expected_bundles - declared_bundles
    results.append(_check(
        "13. manifest `bundles` list contains all 4 canonical portable bundles",
        not missing_b,
        f"declared={len(declared_bundles)}/{len(expected_bundles)}"
        + (f"; missing={sorted(missing_b)}" if missing_b else ""),
    ))

    # 14. manifest runner.stdlib_only == true
    stdlib_declared = False
    if isinstance(manifest, dict) and manifest:
        runner_block = manifest.get("runner", {}) or {}
        stdlib_declared = bool(runner_block.get("stdlib_only"))
    results.append(_check(
        "14. manifest runner.stdlib_only == true",
        stdlib_declared,
        "runner.stdlib_only=true" if stdlib_declared else "missing or false",
    ))

    # 15. manifest cron integration
    cron_ok = False
    if isinstance(manifest, dict) and manifest:
        cron_block = manifest.get("cron_integration", {}) or {}
        cron_ok = (
            cron_block.get("installed") is False
            and "cron.example" in str(cron_block.get("example_path", ""))
        )
    results.append(_check(
        "15. manifest cron_integration.installed==false and example_path contains cron.example",
        cron_ok,
        "installed=false + cron.example present"
        if cron_ok else "cron_integration not configured correctly",
    ))

    # 16. cron.example is dry-run only
    if CRON_EXAMPLE.exists():
        text = CRON_EXAMPLE.read_text(encoding="utf-8")
        lines = text.splitlines()
        real_cron_lines = [
            ln for ln in lines
            if ln.strip()
            and not ln.strip().startswith("#")
            and any(tok in ln for tok in
                    ("/etc/cron.d/", "/var/spool/cron/", "crontab"))
        ]
        is_drop_in = bool(real_cron_lines)
        is_example = (
            "EXAMPLE" in text.upper()
            or "DRY-RUN" in text.upper()
            or "MUST NOT" in text.upper()
            or "NOT installed" in text
            or "not installed" in text.lower()
            or "NOT a real" in text
            or "not a real" in text.lower()
        )
        results.append(_check(
            "16. templates/cron.example exists, marked as example/dry-run, not a real drop-in",
            (not is_drop_in) and is_example,
            "marked as example + no active cron line targeting real cron dir"
            if ((not is_drop_in) and is_example)
            else f"is_drop_in={is_drop_in} is_example={is_example} "
                 f"real_cron_lines={real_cron_lines}",
        ))
    else:
        results.append(_check(
            "16. templates/cron.example exists, marked as example/dry-run, not a real drop-in",
            False, "cron.example missing",
        ))

    # 17. nightly digest JSON at the spec'd default filename
    results.append(_check(
        "17. artifacts/nightly-validation-digest.json exists (spec default filename)",
        DIGEST_JSON.exists(),
        str(DIGEST_JSON.relative_to(REPO)) if DIGEST_JSON.exists() else "missing",
    ))

    # 18. digest overall_status == PASS
    digest: dict = {}
    if DIGEST_JSON.exists():
        digest = _read_json(DIGEST_JSON)
        overall_ok = (isinstance(digest, dict)
                      and digest.get("overall_status") == "PASS")
        results.append(_check(
            "18. digest JSON overall_status == PASS",
            overall_ok,
            f"overall_status={digest.get('overall_status', '?')}"
            if isinstance(digest, dict) else "invalid digest",
        ))
    else:
        results.append(_check(
            "18. digest JSON overall_status == PASS",
            False, "digest JSON missing",
        ))

    # 19. digest blocking checks passed == 9/9 (per the new spec, with
    #     bundles_validatable and cases-json parse as separate checks)
    passed_ok = False
    detail19 = "missing"
    if isinstance(digest, dict) and digest:
        summary = digest.get("summary", {}) or {}
        passed_ok = (
            summary.get("blocking_total") == 9
            and summary.get("passed") == 9
            and summary.get("failed") == 0
        )
        detail19 = (
            f"blocking_total={summary.get('blocking_total')}, "
            f"passed={summary.get('passed')}, "
            f"failed={summary.get('failed')}"
        )
    results.append(_check(
        "19. digest JSON blocking checks passed == 9/9",
        passed_ok, detail19,
    ))

    # 20. digest Markdown at the spec'd default filename
    results.append(_check(
        "20. artifacts/nightly-validation-digest.md exists (spec default filename)",
        DIGEST_MD.exists(),
        str(DIGEST_MD.relative_to(REPO)) if DIGEST_MD.exists() else "missing",
    ))

    # 21. cases.json has ATL-EVOMAP-8A
    phase_ok = False
    detail21 = "missing"
    if DATA_CASES.exists():
        data = _read_json(DATA_CASES)
        case = None
        if isinstance(data, dict):
            case = next(
                (c for c in data.get("cases", [])
                 if c.get("slug") == "evomap-evolver-openclaw-v0"),
                None,
            )
        if case:
            top_phase = str(case.get("phase", ""))
            history = case.get("phase_history", []) or []
            history_phases = [str(h.get("phase", "")) for h in history
                              if isinstance(h, dict)]
            phase_ok = ("ATL-EVOMAP-8A" in top_phase
                        or any("ATL-EVOMAP-8A" in p for p in history_phases))
            detail21 = (f"top_phase={top_phase!r}, "
                        f"history_count={len(history_phases)}")
    results.append(_check(
        "21. data/cases.json phase or phase_history contains ATL-EVOMAP-8A",
        phase_ok, detail21,
    ))

    # 22. backward-compat composite
    prior_validators = [
        ("Phase 5",  REPO / "scripts" / "validate_evomap_phase5_local_evolution_kit.py"),
        ("Phase 6A", REPO / "scripts" / "validate_evomap_phase6a_hermes_systemd_bundle.py"),
        ("Phase 6B", REPO / "scripts" / "validate_evomap_phase6b_telegram_router_bundle.py"),
        ("Phase 6C", REPO / "scripts" / "validate_evomap_phase6c_codex_test_failure_bundle.py"),
        ("Phase 7A", REPO / "scripts" / "validate_evomap_phase7a_domain_signal_injection.py"),
        ("Phase 7B", REPO / "scripts" / "validate_evomap_phase7b_cross_bundle_regression.py"),
    ]
    failed_prior: list[str] = []
    for name, vp in prior_validators:
        if not vp.exists():
            failed_prior.append(f"{name}: missing")
            continue
        try:
            r = subprocess.run(
                ["python3", str(vp)],
                cwd=str(REPO), capture_output=True, text=True, timeout=60,
            )
            if "ALL CHECKS PASSED" not in r.stdout:
                failed_prior.append(f"{name}: rc={r.returncode}")
        except Exception as exc:
            failed_prior.append(f"{name}: {exc}")

    # Self-host: nightly runner smoke
    self_host_ok = True
    self_host_detail = "skipped (runner missing)"
    if RUNNER.exists():
        try:
            r = subprocess.run(
                ["python3", str(RUNNER), "--repo-root", "."],
                cwd=str(REPO), capture_output=True, text=True, timeout=180,
            )
            self_host_ok = r.returncode == 0
            self_host_detail = f"rc={r.returncode}"
        except Exception as exc:
            self_host_ok = False
            self_host_detail = f"runner exec failed: {exc}"

    composite_ok = (not failed_prior) and self_host_ok
    composite_detail = (
        f"6_prior_validators={'PASS' if not failed_prior else failed_prior}, "
        f"nightly_runner_self_host={self_host_detail}"
    )
    results.append(_check(
        "22. prior validators (5, 6A, 6B, 6C, 7A, 7B) ALL CHECKS PASSED "
        "+ nightly runner self-host exits 0 (backward-compat composite)",
        composite_ok, composite_detail,
    ))

    # ---- summary ----
    passes = sum(1 for r in results if r["ok"])
    fails = sum(1 for r in results if not r["ok"])
    print("ATL-EVOMAP-8A Nightly Validation Loop Asset — Validator")
    print(f"  total: {len(results)} checks")
    print(f"  PASS:  {passes}")
    print(f"  FAIL:  {fails}")
    print()
    for r in results:
        marker = "PASS" if r["ok"] else "FAIL"
        print(f"  [{marker}] {r['name']}")
        if r["detail"]:
            print(f"          {r['detail']}")
    print()
    if fails == 0:
        print("PASS  ALL CHECKS PASSED")
        print("Case: evomap-evolver-openclaw-v0 (Phase 8A Nightly Validation Loop)")
        try:
            data = _read_json(DATA_CASES)
            case = next((c for c in data.get("cases", [])
                         if c.get("slug") == "evomap-evolver-openclaw-v0"), None)
            if case:
                print(f"Status: {case.get('status', '?')} "
                      f"({case.get('final_status', '?')})")
        except Exception:
            pass
        return 0
    else:
        print(f"FAIL  {fails} CHECKS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
