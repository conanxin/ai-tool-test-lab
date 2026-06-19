#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_evomap_phase9b_curator_nightly_integration.py — Validator for
ATL-EVOMAP-9B (Curator-to-Nightly Integration).

Phase: ATL-EVOMAP-9B
Base:  7811e1b (post-ATL-EVOMAP-9A curator skill)

Verifies, in order:

  1. File presence (runner, manifest, 9A sample bundle, digest JSON /
     MD / run-log, 9B README, 9B case report, 9B top-level report,
     9B validator script).
  2. Manifest JSON parse + schema_version + canary_bundles[] presence.
  3. Manifest declares at least one canary bundle, with id /
     source_phase / path / lane / blocking=false / expected_status.
  4. Runner (scripts/evomap_nightly_validate.py) is stdlib-only
     (AST check) and references `canary` (i.e. supports the lane).
  5. Digest JSON parse + overall_status == PASS + summary fields.
  6. Digest canary_summary: total >= 1, passed >= 1, failed == 0,
     status == CANARY_PASS, blocking_failures == 0.
  7. Digest canary_bundle_checks[0]: id points at the 9A sample bundle,
     blocking == False, inspect/validate/apply_dry_run all PASS.
  8. Canonical bundle_checks.inspect / validate length == 4.
  9. Top-level validators[] length == 7 and all PASS.
 10. Secret scan clean (digest secret_scan_clean row PASS, hits == 0).
 11. Git hygiene clean (digest git_hygiene row PASS, no root .evolver/
     or memory/ tracked).
 12. Hard boundaries all YES in digest.
 13. cases.json top-level phase contains ATL-EVOMAP-9B and
     phase_history has a 9B entry.
 14. data/cases.json top-level phase or phase_history contains ATL-EVOMAP-9B.
 15. Main case README contains ATL-EVOMAP-9B.
 16. No real cron installed: cron.example is still EXAMPLE and not a
     drop-in to /etc/cron.d or systemd timer dir; no new
     /etc/cron.d / systemd artifact introduced by this phase.
 17. git status: no root .evolver/ or memory/ tracked (defense-in-depth
     alongside the digest row).
 18. Prior validators (5, 6A, 6B, 6C, 7A, 7B, 8A, 9A) all ALL CHECKS PASSED.

Exit codes:
  0 — all checks passed
  1 — at least one check failed
  2 — invocation / IO error

stdlib only.
"""

from __future__ import annotations

import ast
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (REPO / "cases" / "evomap-evolver-openclaw-v0"
                 / "phase8a-nightly-validation-loop"
                 / "validation-loop-manifest.json")

RUNNER_PATH = REPO / "scripts" / "evomap_nightly_validate.py"

SAMPLE_BUNDLE = (REPO / "cases" / "evomap-evolver-openclaw-v0"
                 / "phase9a-bundle-curator-skill" / "generated"
                 / "sample-safe-bundle.bundle.json")

DIGEST_DIR = (REPO / "cases" / "evomap-evolver-openclaw-v0"
              / "phase9b-curator-nightly-integration" / "artifacts"
              / "nightly-smoke")

DIGEST_JSON = DIGEST_DIR / "nightly-validation-digest.json"
DIGEST_MD = DIGEST_DIR / "nightly-validation-digest.md"
DIGEST_LOG = DIGEST_DIR / "nightly-validation-run.log"

CASE_README_9B = (REPO / "cases" / "evomap-evolver-openclaw-v0"
                  / "phase9b-curator-nightly-integration" / "README.md")

CASE_REPORT_9B = (REPO / "cases" / "evomap-evolver-openclaw-v0"
                  / "phase9b-curator-nightly-integration"
                  / "ATL_EVOMAP_9B_CURATOR_NIGHTLY_INTEGRATION_REPORT.md")

TOP_REPORT_9B = (REPO / "reports"
                 / "ATL_EVOMAP_9B_CURATOR_NIGHTLY_INTEGRATION_REPORT.md")

VALIDATOR_9B_PATH = (REPO / "scripts"
                     / "validate_evomap_phase9b_curator_nightly_integration.py")

CRON_EXAMPLE = (REPO / "cases" / "evomap-evolver-openclaw-v0"
                / "phase8a-nightly-validation-loop" / "templates"
                / "cron.example")

DATA_CASES = REPO / "data" / "cases.json"

MAIN_README = REPO / "README.md"

# Allowed stdlib top-level imports for the runner
_ALLOWED_RUNNER_TOP_IMPORTS = {
    "argparse", "datetime", "json", "mimetypes", "os", "re", "subprocess",
    "sys", "textwrap", "traceback", "pathlib", "typing", "__future__",
}


PASS_LIST: list[str] = []
FAIL_LIST: list[str] = []


def record(idx: int, label: str, ok: bool, detail: str = "") -> None:
    tag = "\033[92mPASS\033[0m" if ok else "\033[91mFAIL\033[0m"
    msg = f"  [{tag}] {idx:>2}. {label}"
    if detail:
        msg += f"\n          {detail}"
    print(msg, flush=True)
    (PASS_LIST if ok else FAIL_LIST).append(label)


def _now() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot parse {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Check 1: File presence
# ---------------------------------------------------------------------------

def check_file_presence() -> None:
    print("=== File presence ===", flush=True)
    idx = 1

    record(idx, "scripts/evomap_nightly_validate.py exists",
           RUNNER_PATH.is_file(),
           str(RUNNER_PATH))
    idx += 1

    record(idx, "validation-loop-manifest.json exists",
           MANIFEST_PATH.is_file(),
           str(MANIFEST_PATH))
    idx += 1

    record(idx, "9A sample-safe-bundle.bundle.json exists",
           SAMPLE_BUNDLE.is_file(),
           str(SAMPLE_BUNDLE))
    idx += 1

    record(idx, "nightly-validation-digest.json exists (smoke artifact)",
           DIGEST_JSON.is_file(),
           str(DIGEST_JSON))
    idx += 1

    record(idx, "nightly-validation-digest.md exists (smoke artifact)",
           DIGEST_MD.is_file(),
           str(DIGEST_MD))
    idx += 1

    record(idx, "nightly-validation-run.log exists (smoke artifact)",
           DIGEST_LOG.is_file(),
           str(DIGEST_LOG))
    idx += 1

    record(idx, "cases/.../phase9b-curator-nightly-integration/README.md exists",
           CASE_README_9B.is_file(),
           str(CASE_README_9B))
    idx += 1

    record(idx, "cases/.../ATL_EVOMAP_9B_CURATOR_NIGHTLY_INTEGRATION_REPORT.md exists",
           CASE_REPORT_9B.is_file(),
           str(CASE_REPORT_9B))
    idx += 1

    record(idx, "reports/ATL_EVOMAP_9B_CURATOR_NIGHTLY_INTEGRATION_REPORT.md exists",
           TOP_REPORT_9B.is_file(),
           str(TOP_REPORT_9B))
    idx += 1

    record(idx, "scripts/validate_evomap_phase9b_curator_nightly_integration.py exists",
           VALIDATOR_9B_PATH.is_file(),
           str(VALIDATOR_9B_PATH))
    idx += 1


# ---------------------------------------------------------------------------
# Check 2-4: Manifest, sample bundle, runner source
# ---------------------------------------------------------------------------

def check_manifest() -> None:
    print("\n=== Manifest extension ===", flush=True)
    idx = 11
    if not MANIFEST_PATH.is_file():
        record(idx, "manifest JSON parses", False, "missing")
        return
    try:
        manifest = _read_json(MANIFEST_PATH)
    except Exception as exc:
        record(idx, "manifest JSON parses", False, str(exc))
        return
    record(idx, "manifest JSON parses", True, f"keys={len(manifest)}")
    idx += 1

    schema = str(manifest.get("schema_version", ""))
    record(idx,
           "manifest schema_version == 'atl-evomap-nightly-validation-v0.1'",
           schema == "atl-evomap-nightly-validation-v0.1",
           f"schema_version={schema!r}")
    idx += 1

    cb = manifest.get("canary_bundles", None)
    record(idx, "manifest contains `canary_bundles` (list or empty)",
           isinstance(cb, list),
           f"type={type(cb).__name__}, len={len(cb) if isinstance(cb, list) else '-'}")
    idx += 1

    if isinstance(cb, list) and cb:
        record(idx, "manifest `canary_bundles` length >= 1",
               len(cb) >= 1,
               f"len={len(cb)}")
        idx += 1
        # First entry points at the 9A sample bundle
        first = cb[0]
        first_path = str(first.get("path", ""))
        record(idx,
               "first canary bundle path points at sample-safe-bundle.bundle.json",
               first_path.endswith("sample-safe-bundle.bundle.json"),
               f"path={first_path!r}")
        idx += 1
        record(idx,
               "first canary bundle blocking == False (non-blocking lane)",
               first.get("blocking", None) is False,
               f"blocking={first.get('blocking')!r}")
        idx += 1
        record(idx,
               "first canary bundle lane == 'curator_generated'",
               first.get("lane") == "curator_generated",
               f"lane={first.get('lane')!r}")
        idx += 1
        record(idx,
               "first canary bundle expected_status == 'CANARY_PASS'",
               first.get("expected_status") == "CANARY_PASS",
               f"expected_status={first.get('expected_status')!r}")
        idx += 1


def check_sample_bundle() -> None:
    print("\n=== Sample canary bundle ===", flush=True)
    idx = 19
    if not SAMPLE_BUNDLE.is_file():
        record(idx, "sample-safe-bundle.bundle.json JSON parses", False, "missing")
        return
    try:
        b = _read_json(SAMPLE_BUNDLE)
    except Exception as exc:
        record(idx, "sample-safe-bundle.bundle.json JSON parses", False, str(exc))
        return
    record(idx, "sample-safe-bundle.bundle.json JSON parses", True,
           f"top-level keys={len(b)}")
    idx += 1
    record(idx, "sample bundle schema_version == portable-bundle-v0.1",
           str(b.get("schema_version", "")).endswith("portable-bundle-v0.1"),
           f"schema_version={b.get('schema_version')!r}")
    idx += 1


def check_runner_source() -> None:
    print("\n=== Runner source (stdlib-only + canary lane marker) ===",
          flush=True)
    idx = 21
    if not RUNNER_PATH.is_file():
        record(idx, "runner source exists", False, "missing")
        return
    try:
        src = RUNNER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        record(idx, "runner source read", False, str(exc))
        return
    record(idx, "runner source read", True, f"{len(src)} chars")
    idx += 1

    # AST parse
    try:
        tree = ast.parse(src, filename=str(RUNNER_PATH))
    except SyntaxError as exc:
        record(idx, "runner AST parses", False, str(exc))
        return
    record(idx, "runner AST parses", True, "ok")
    idx += 1

    # Stdlib-only guard via AST imports
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = (alias.name or "").split(".")[0]
                if top and top not in _ALLOWED_RUNNER_TOP_IMPORTS:
                    bad.append(top)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0] if mod else ""
            if top and top not in _ALLOWED_RUNNER_TOP_IMPORTS:
                bad.append(top)
    record(idx, "runner is stdlib-only (AST top-level imports)",
           not bad,
           "non-stdlib: " + ", ".join(sorted(set(bad))) if bad else "ok")
    idx += 1

    # Source keyword check: must mention 'canary' (canary lane marker)
    lower = src.lower()
    record(idx,
           "runner source references 'canary' (canary lane present)",
           "canary" in lower,
           "found: canary" if "canary" in lower else "missing")
    idx += 1

    # Required CLI flags preserved (backward compat)
    required_flags = ["--repo-root", "--out-dir", "--markdown-name",
                      "--json-name", "--strict", "--dry-run",
                      "--output-dir"]
    missing_flags = [f for f in required_flags
                     if f not in src]
    record(idx,
           "runner preserves 8A CLI flags (backward compat)",
           not missing_flags,
           ("missing: " + ", ".join(missing_flags))
           if missing_flags
           else "all 7 flags present")
    idx += 1


# ---------------------------------------------------------------------------
# Check 5-12: Digest contents
# ---------------------------------------------------------------------------

def check_digest() -> None:
    print("\n=== Digest contents ===", flush=True)
    idx = 26
    if not DIGEST_JSON.is_file():
        record(idx, "digest JSON exists", False, "missing")
        return
    try:
        d = _read_json(DIGEST_JSON)
    except Exception as exc:
        record(idx, "digest JSON parses", False, str(exc))
        return
    record(idx, "digest JSON parses", True,
           f"schema_version={d.get('schema_version')!r}")
    idx += 1

    overall = str(d.get("overall_status", ""))
    record(idx, "digest overall_status == PASS",
           overall == "PASS",
           f"overall_status={overall!r}")
    idx += 1

    summary = d.get("summary", {}) or {}
    record(idx,
           "digest summary.blocking_total == 9 (unchanged from 8A)",
           summary.get("blocking_total") == 9,
           f"blocking_total={summary.get('blocking_total')}")
    idx += 1
    record(idx,
           "digest summary.passed == 9 and failed == 0",
           (summary.get("passed") == 9 and summary.get("failed") == 0),
           f"passed={summary.get('passed')}, failed={summary.get('failed')}")
    idx += 1
    record(idx,
           "digest summary.non_blocking == 1 (canary row)",
           summary.get("non_blocking") == 1,
           f"non_blocking={summary.get('non_blocking')}")
    idx += 1

    # bundle_checks
    bc = d.get("bundle_checks", {}) or {}
    record(idx, "digest.bundle_checks.inspect length == 4 (canonical)",
           len(bc.get("inspect", [])) == 4,
           f"len={len(bc.get('inspect', []))}")
    idx += 1
    record(idx, "digest.bundle_checks.validate length == 4 (canonical)",
           len(bc.get("validate", [])) == 4,
           f"len={len(bc.get('validate', []))}")
    idx += 1

    ins_pass = all(
        e.get("status") == "PASS" for e in bc.get("inspect", []))
    record(idx, "digest.bundle_checks.inspect all status == PASS",
           ins_pass,
           f"statuses={[e.get('status') for e in bc.get('inspect', [])]}")
    idx += 1
    val_pass = all(
        e.get("status") == "PASS" for e in bc.get("validate", []))
    record(idx, "digest.bundle_checks.validate all status == PASS",
           val_pass,
           f"statuses={[e.get('status') for e in bc.get('validate', [])]}")
    idx += 1

    # validators[] top-level
    validators = d.get("validators", []) or []
    record(idx, "digest.validators top-level length >= 7",
           len(validators) >= 7,
           f"len={len(validators)}")
    idx += 1
    val_pass_all = (len(validators) > 0
                    and all(v.get("status") == "PASS" for v in validators))
    record(idx, "digest.validators all status == PASS",
           val_pass_all,
           f"statuses={[v.get('status') for v in validators]}")
    idx += 1

    # canary_summary
    cs = d.get("canary_summary", {}) or {}
    record(idx, "digest.canary_summary.total >= 1",
           cs.get("total", 0) >= 1,
           f"total={cs.get('total')}")
    idx += 1
    record(idx, "digest.canary_summary.passed >= 1",
           cs.get("passed", 0) >= 1,
           f"passed={cs.get('passed')}")
    idx += 1
    record(idx, "digest.canary_summary.failed == 0",
           cs.get("failed", 0) == 0,
           f"failed={cs.get('failed')}")
    idx += 1
    record(idx, "digest.canary_summary.status == 'CANARY_PASS'",
           cs.get("status") == "CANARY_PASS",
           f"status={cs.get('status')!r}")
    idx += 1
    record(idx,
           "digest.canary_summary.blocking_failures == 0",
           cs.get("blocking_failures", -1) == 0,
           f"blocking_failures={cs.get('blocking_failures')}")
    idx += 1

    # canary_bundle_checks[0]
    cbc = d.get("canary_bundle_checks", []) or []
    record(idx, "digest.canary_bundle_checks length >= 1",
           len(cbc) >= 1,
           f"len={len(cbc)}")
    idx += 1
    if cbc:
        first = cbc[0]
        record(idx,
               "canary_bundle_checks[0].blocking == False (non-blocking)",
               first.get("blocking") is False,
               f"blocking={first.get('blocking')!r}")
        idx += 1
        record(idx,
               "canary_bundle_checks[0].id points at 9A sample bundle",
               str(first.get("id", "")).endswith("sample-safe-bundle-phase9a")
               or "sample-safe-bundle" in str(first.get("path", "")),
               f"id={first.get('id')!r}, path={first.get('path')!r}")
        idx += 1
        record(idx,
               "canary_bundle_checks[0].inspect.status == PASS",
               (first.get("inspect", {}) or {}).get("status") == "PASS",
               f"inspect.status={(first.get('inspect') or {}).get('status')}")
        idx += 1
        record(idx,
               "canary_bundle_checks[0].validate.status == PASS",
               (first.get("validate", {}) or {}).get("status") == "PASS",
               f"validate.status={(first.get('validate') or {}).get('status')}")
        idx += 1
        record(idx,
               "canary_bundle_checks[0].apply_dry_run.status == PASS",
               (first.get("apply_dry_run", {}) or {}).get("status") == "PASS",
               f"apply_dry_run.status="
               f"{(first.get('apply_dry_run') or {}).get('status')}")
        idx += 1
        record(idx,
               "canary_bundle_checks[0].status == 'CANARY_PASS'",
               first.get("status") == "CANARY_PASS",
               f"status={first.get('status')!r}")
        idx += 1
        target_rt = str(
            (first.get("apply_dry_run", {}) or {}).get("target_runtime", ""))
        record(idx,
               "canary apply_dry_run.target_runtime is /tmp/... (isolated)",
               target_rt.startswith("/tmp/"),
               f"target_runtime={target_rt!r}")
        idx += 1

    # Secret scan
    checks = d.get("checks", []) or []
    sec_row = next((c for c in checks
                    if c.get("check_id") == "secret_scan_clean"), None)
    sec_ok = bool(sec_row and sec_row.get("status") == "PASS")
    sec_hits = 0
    if sec_row and isinstance(sec_row.get("extra"), dict):
        hits = (sec_row["extra"].get("hits") or {})
        sec_hits = sum(len(v) for v in hits.values() if isinstance(v, list))
    record(idx, "digest secret_scan_clean row PASS",
           sec_ok,
           f"hits={sec_hits}")
    idx += 1
    record(idx, "digest secret_scan hits == 0",
           sec_hits == 0,
           f"hits={sec_hits}")
    idx += 1

    # Git hygiene
    git_row = next((c for c in checks
                    if c.get("check_id") == "git_hygiene_no_root_evolver_or_memory"),
                   None)
    git_ok = bool(git_row and git_row.get("status") == "PASS")
    record(idx, "digest git_hygiene_no_root_evolver_or_memory row PASS",
           git_ok,
           f"status={(git_row or {}).get('status')}")
    idx += 1

    # Hard boundaries
    hb = d.get("hard_boundaries", {}) or {}
    hb_all_true = bool(hb) and all(bool(v) for v in hb.values())
    record(idx,
           f"digest.hard_boundaries all YES ({len(hb)} fields)",
           hb_all_true,
           ("all YES" if hb_all_true
            else f"non-true: {[k for k,v in hb.items() if not v]}"))
    idx += 1


# ---------------------------------------------------------------------------
# Check 13-15: cases.json + main README
# ---------------------------------------------------------------------------

def check_cases_and_readme() -> None:
    print("\n=== cases.json + main README ===", flush=True)
    idx = 50
    if not DATA_CASES.is_file():
        record(idx, "data/cases.json exists", False, "missing")
        return
    try:
        data = _read_json(DATA_CASES)
    except Exception as exc:
        record(idx, "data/cases.json parses", False, str(exc))
        return
    record(idx, "data/cases.json parses", True,
           f"top keys={len(data) if isinstance(data, dict) else 'n/a'}")
    idx += 1

    case = None
    if isinstance(data, dict):
        case = next(
            (c for c in data.get("cases", [])
             if c.get("slug") == "evomap-evolver-openclaw-v0"),
            None,
        )
    record(idx, "evomap-evolver-openclaw-v0 case present",
           case is not None,
           f"case={case is not None}")
    idx += 1

    if case:
        top_phase = str(case.get("phase", ""))
        history = case.get("phase_history", []) or []
        history_phases = [str(h.get("phase", "")) for h in history
                          if isinstance(h, dict)]
        ok_top = "ATL-EVOMAP-9B" in top_phase
        ok_hist = any("ATL-EVOMAP-9B" in p for p in history_phases)
        record(idx,
               "data/cases.json phase or phase_history contains ATL-EVOMAP-9B",
               ok_top or ok_hist,
               f"top_phase={top_phase!r}, history_count={len(history_phases)}")
        idx += 1

        final = str(case.get("final_status", ""))
        record(idx,
               "data/cases.json final_status looks like 9B final",
               ("CURATOR_NIGHTLY" in final or "9B" in final or "INTEGRATION" in final),
               f"final_status={final!r}")
        idx += 1

    if MAIN_README.is_file():
        text = MAIN_README.read_text(encoding="utf-8", errors="replace")
        record(idx, "main README references ATL-EVOMAP-9B",
               "ATL-EVOMAP-9B" in text,
               f"len={len(text)}")
        idx += 1
    else:
        record(idx, "main README exists", False, "missing")
        idx += 1


# ---------------------------------------------------------------------------
# Check 16-17: No real cron + git hygiene defense-in-depth
# ---------------------------------------------------------------------------

def check_no_real_cron_and_git() -> None:
    print("\n=== No real cron + git hygiene ===", flush=True)
    idx = 55

    # cron.example is still EXAMPLE (not a real drop-in)
    if CRON_EXAMPLE.is_file():
        text = CRON_EXAMPLE.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        is_example = (
            "example" in lower
            or "dry-run" in lower
            or "this is a sample" in lower
            or "do not install" in lower
            or "# sample" in lower
            or "# example" in lower
        )
        record(idx, "cron.example still marked as EXAMPLE / dry-run",
               is_example,
               f"len={len(text)}")
    else:
        record(idx, "cron.example exists", False, "missing")
    idx += 1

    # No active crontab line targeting real cron dir
    # (sanity check: no /etc/cron.d line in any new file we created)
    new_files = [
        CASE_README_9B, CASE_REPORT_9B, TOP_REPORT_9B, DIGEST_JSON,
        DIGEST_MD, DIGEST_LOG,
    ]
    bad_active = []
    for f in new_files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for ln in text.splitlines():
            low = ln.lower().strip()
            if (low.startswith("* ")
                    and "/etc/cron" in low
                    and "example" not in low
                    and "do not" not in low
                    and "not installed" not in low):
                bad_active.append(f"{f}: {ln[:80]}")
    record(idx,
           "no real crontab drop-in line in any 9B file",
           not bad_active,
           ("hits: " + "; ".join(bad_active[:3]))
           if bad_active
           else "clean")
    idx += 1

    # No real systemd timer artifact
    systemd_hits: list[str] = []
    for f in new_files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for ln in text.splitlines():
            low = ln.lower().strip()
            if "/etc/systemd/system" in low and "not installed" not in low:
                if "would-create" in low or "expected_drop_in_path" in low:
                    continue
                systemd_hits.append(f"{f}: {ln[:80]}")
    record(idx,
           "no real systemd timer drop-in line in any 9B file",
           not systemd_hits,
           ("hits: " + "; ".join(systemd_hits[:3]))
           if systemd_hits
           else "clean")
    idx += 1

    # Git hygiene: no root .evolver/ or memory/ tracked
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(REPO),
            capture_output=True,
            check=False,
            timeout=30,
            env={**os.environ, "A2A_HUB_URL": ""},
        )
        out = proc.stdout.decode("utf-8", errors="replace")
    except Exception as exc:
        record(idx, "git ls-files ran", False, str(exc))
        return
    tracked = [p for p in out.split("\x00") if p]
    bad = [
        p for p in tracked
        if p.startswith(".evolver/") or p == ".evolver"
        or p.startswith("memory/")
    ]
    record(idx,
           "no root .evolver/ or memory/ tracked by git (defense-in-depth)",
           not bad,
           f"bad_paths={bad[:3] if bad else 'none'}")
    idx += 1


# ---------------------------------------------------------------------------
# Check 18: Prior validators
# ---------------------------------------------------------------------------

def check_prior_validators() -> None:
    print("\n=== Prior validators (5, 6A, 6B, 6C, 7A, 7B, 8A, 9A) ===",
          flush=True)
    idx = 60
    validators = [
        ("Phase 5",  REPO / "scripts" / "validate_evomap_phase5_local_evolution_kit.py"),
        ("Phase 6A", REPO / "scripts" / "validate_evomap_phase6a_hermes_systemd_bundle.py"),
        ("Phase 6B", REPO / "scripts" / "validate_evomap_phase6b_telegram_router_bundle.py"),
        ("Phase 6C", REPO / "scripts" / "validate_evomap_phase6c_codex_test_failure_bundle.py"),
        ("Phase 7A", REPO / "scripts" / "validate_evomap_phase7a_domain_signal_injection.py"),
        ("Phase 7B", REPO / "scripts" / "validate_evomap_phase7b_cross_bundle_regression.py"),
        ("Phase 8A", REPO / "scripts" / "validate_evomap_phase8a_nightly_validation_loop.py"),
        ("Phase 9A", REPO / "scripts" / "validate_evomap_phase9a_bundle_curator_skill.py"),
    ]
    for name, vp in validators:
        if not vp.is_file():
            record(idx, f"{name} validator passes", False, "missing")
            idx += 1
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(vp)],
                cwd=str(REPO),
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "A2A_HUB_URL": ""},
            )
            text = (proc.stdout or "") + (proc.stderr or "")
            ok = (proc.returncode == 0
                  and "ALL CHECKS PASSED" in text)
            last_line = next(
                (ln.strip() for ln in reversed(text.splitlines())
                 if ln.strip()), "")
            detail = (f"rc={proc.returncode}, last_line={last_line[:80]!r}"
                      if not ok else "")
            record(idx, f"{name} validator passes", ok, detail)
        except subprocess.TimeoutExpired:
            record(idx, f"{name} validator passes", False, "timeout")
        except Exception as exc:
            record(idx, f"{name} validator passes", False, str(exc))
        idx += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"=== validate_evomap_phase9b_curator_nightly_integration.py ===")
    print(f"REPO         : {REPO}")
    print(f"DIGEST_JSON  : {DIGEST_JSON}")
    print(f"Generated at : {_now()}")
    print()

    check_file_presence()
    check_manifest()
    check_sample_bundle()
    check_runner_source()
    check_digest()
    check_cases_and_readme()
    check_no_real_cron_and_git()
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
    print("Case: evomap-evolver-openclaw-v0 (Phase 9B Curator-to-Nightly "
          "Integration)")
    print("Status: curator nightly integration smoke pass "
          "(CURATOR_NIGHTLY_INTEGRATION_SMOKE_PASS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())