#!/usr/bin/env python3
"""ATL-EVOMAP-6D validator — Browser-Control Recovery Bundle.

Stdlib only. 33 checks; non-fatal warnings only for a small set of
non-blocking meta fields. Verifies:
  - offline fixture + parser + safety self-tests
  - Gene / Capsule / portable bundle structure
  - inspect / validate outputs
  - apply dry-run / --yes outputs and target summary
  - nightly manifest extension
  - nightly smoke result (5 canonical + 1 canary)
  - secret scan / git hygiene
  - all prior phase validators still PASS
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CASE_DIR = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase6d-browser-control-bundle"
FIXTURE = CASE_DIR / "fixtures" / "browser-control-recovery-sample.txt"
BUNDLE = CASE_DIR / "bundle" / "browser-control-recovery.bundle.json"
GENE = CASE_DIR / "artifacts" / "gene-browser-control-recovery.json"
CAPSULE = CASE_DIR / "artifacts" / "capsule-browser-control-recovery.json"
PARSER_OUTPUT = CASE_DIR / "artifacts" / "browser-control-fixture-output.json"
SELFTEST_AUTH = CASE_DIR / "artifacts" / "parser-selftest-auth-output.json"
SELFTEST_COOKIE = CASE_DIR / "artifacts" / "parser-selftest-cookie-output.json"
SELFTEST_ENV = CASE_DIR / "artifacts" / "parser-selftest-env-path-output.json"
INSPECT = CASE_DIR / "artifacts" / "inspect-browser-control-bundle-output.json"
VALIDATE = CASE_DIR / "artifacts" / "validate-browser-control-bundle-output.json"
APPLY_DRY = CASE_DIR / "artifacts" / "apply-browser-control-bundle-dry-run-output.json"
APPLY_YES = CASE_DIR / "artifacts" / "apply-browser-control-bundle-yes-output.json"
APPLY_SUMMARY = CASE_DIR / "artifacts" / "apply-browser-control-target-summary.json"
SMOKE_DIGEST = CASE_DIR / "artifacts" / "nightly-smoke" / "nightly-validation-digest.json"
SMOKE_SUMMARY = CASE_DIR / "artifacts" / "nightly-6d-smoke-summary.json"
CASE_REPORT = CASE_DIR / "ATL_EVOMAP_6D_BROWSER_CONTROL_BUNDLE_REPORT.md"
TOP_REPORT = REPO_ROOT / "reports" / "ATL_EVOMAP_6D_BROWSER_CONTROL_BUNDLE_REPORT.md"
MANIFEST = REPO_ROOT / "cases" / "evomap-evolver-openclaw-v0" / "phase8a-nightly-validation-loop" / "validation-loop-manifest.json"
MAIN_README = REPO_ROOT / "README.md"
CASE_README = CASE_DIR / "README.md"
PARSER = REPO_ROOT / "scripts" / "browser_control_recovery_fixture.py"

REQUIRED_TARGET_SIGNALS = {
    "browser_control_failure",
    "browser_control_port_unavailable",
    "browser_control_auth_missing",
    "browser_launch_timeout",
    "screenshot_missing",
    "terminal_page_evidence_missing",
    "browser_control_failure:openclaw",
    "browser_control_port_unavailable:18791",
}

PRIOR_VALIDATORS = [
    "validate_evomap_phase5_local_evolution_kit.py",
    "validate_evomap_phase6a_hermes_systemd_bundle.py",
    "validate_evomap_phase6b_telegram_router_bundle.py",
    "validate_evomap_phase6c_codex_test_failure_bundle.py",
    "validate_evomap_phase7a_domain_signal_injection.py",
    "validate_evomap_phase7b_cross_bundle_regression.py",
    "validate_evomap_phase8a_nightly_validation_loop.py",
    "validate_evomap_phase9a_bundle_curator_skill.py",
    "validate_evomap_phase9b_curator_nightly_integration.py",
]


def _record(results, name, status, detail=""):
    results.append({"check_id": name, "status": status, "detail": detail})


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def check_parser_and_fixture(results):
    if not PARSER.exists():
        _record(results, "01.parser_script_exists", "FAIL", str(PARSER))
    else:
        _record(results, "01.parser_script_exists", "PASS")

    if not FIXTURE.exists():
        _record(results, "02.fixture_exists", "FAIL", str(FIXTURE))
        return

    _record(results, "02.fixture_exists", "PASS")
    fixture_size = FIXTURE.stat().st_size
    if fixture_size < 500:
        _record(results, "03.fixture_non_trivial", "FAIL", f"size={fixture_size}")
    else:
        _record(results, "03.fixture_non_trivial", "PASS", f"size={fixture_size}")

    if not PARSER_OUTPUT.exists():
        _record(results, "04.parser_output_exists", "FAIL", str(PARSER_OUTPUT))
        return
    try:
        out = _read_json(PARSER_OUTPUT)
    except Exception as e:
        _record(results, "04.parser_output_json", "FAIL", f"parse_error: {e}")
        return

    _record(results, "04.parser_output_json", "PASS")
    _record(results, "05.parser_output_ok_true", "PASS" if out.get("ok") else "FAIL", f"ok={out.get('ok')}")

    for k in [
        "browser_control_failure",
        "browser_control_port_unavailable",
        "browser_control_auth_missing",
        "browser_launch_timeout",
        "screenshot_missing",
        "terminal_page_evidence_missing",
    ]:
        v = out.get(k)
        _record(
            results,
            f"06.parser_output.{k}",
            "PASS" if v is True else "FAIL",
            f"value={v}",
        )

    sigs = out.get("failure_signatures") or []
    expected_sigs = {
        "browser_control_port_unavailable_18791",
        "browser_control_auth_missing",
        "browser_launch_timeout",
    }
    missing = expected_sigs - set(sigs)
    _record(
        results,
        "07.parser_output.failure_signatures",
        "PASS" if not missing else "FAIL",
        f"missing={sorted(missing)}" if missing else f"count={len(sigs)}",
    )

    safety = out.get("safety") or {}
    all_safe = bool(safety) and all(bool(v) for v in safety.values())
    _record(
        results,
        "08.parser_output.safety_all_true",
        "PASS" if all_safe else "FAIL",
        f"fields={list(safety.keys())}",
    )


def check_parser_selftests(results):
    artifacts = {
        "auth": (SELFTEST_AUTH, "unsafe_fixture"),
        "cookie": (SELFTEST_COOKIE, "unsafe_fixture"),
        "env_path": (SELFTEST_ENV, "refused_input_path"),
    }
    for name, (path, expected_reason) in artifacts.items():
        if not path.exists():
            _record(results, f"09.selftest_{name}_exists", "FAIL", str(path))
            continue
        try:
            data = _read_json(path)
        except Exception as e:
            _record(results, f"09.selftest_{name}_json", "FAIL", f"parse_error: {e}")
            continue
        _record(results, f"09.selftest_{name}_exists", "PASS")
        ok = data.get("ok")
        reason = (data.get("reason") or "")
        is_reject = (ok is False) and (expected_reason in reason)
        _record(
            results,
            f"10.selftest_{name}_rejected",
            "PASS" if is_reject else "FAIL",
            f"ok={ok} reason={reason!r}",
        )
        # No raw unsafe string should appear in the artifact.
        # We use a generous minimum length to avoid matching normal words.
        raw_blob = json.dumps(data)
        bad_substrings = [
            "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",  # 40 'Z's
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",  # 40 'C's
        ]
        leaked = [s for s in bad_substrings if s in raw_blob]
        _record(
            results,
            f"11.selftest_{name}_no_raw_unsafe",
            "PASS" if not leaked else "FAIL",
            f"leaked={leaked}" if leaked else "ok",
        )


def check_gene(results):
    if not GENE.exists():
        _record(results, "12.gene_artifact_exists", "FAIL", str(GENE))
        return
    try:
        g = _read_json(GENE)
    except Exception as e:
        _record(results, "12.gene_artifact_json", "FAIL", f"parse_error: {e}")
        return
    _record(results, "12.gene_artifact_exists", "PASS")
    gid = g.get("id")
    _record(
        results,
        "13.gene_id_correct",
        "PASS" if gid == "gene_distilled_browser-control-recovery" else "FAIL",
        f"id={gid}",
    )
    expected_signals = {
        "browser_control_failure",
        "browser_control_port_unavailable",
        "browser_control_auth_missing",
        "browser_launch_timeout",
        "screenshot_missing",
        "terminal_page_evidence_missing",
        "fallback_bypass_attempted",
    }
    got = set(g.get("signals_match", []))
    missing = expected_signals - got
    _record(
        results,
        "14.gene_signals_match_present",
        "PASS" if not missing else "FAIL",
        f"missing={sorted(missing)}" if missing else f"count={len(got)}",
    )
    forbidden = g.get("constraints", {}).get("forbidden_actions", [])
    need = "launch_real_browser_from_fixture_parser" in forbidden and \
        "read_env_file" in forbidden and \
        "curl_or_raw_http_bypass" in forbidden
    _record(
        results,
        "15.gene_forbidden_actions_present",
        "PASS" if need else "FAIL",
        f"forbidden_actions_count={len(forbidden)}",
    )


def check_capsule(results):
    if not CAPSULE.exists():
        _record(results, "16.capsule_artifact_exists", "FAIL", str(CAPSULE))
        return
    try:
        c = _read_json(CAPSULE)
    except Exception as e:
        _record(results, "16.capsule_artifact_json", "FAIL", f"parse_error: {e}")
        return
    _record(results, "16.capsule_artifact_exists", "PASS")
    cid = c.get("id")
    _record(
        results,
        "17.capsule_id_correct",
        "PASS" if cid == "capsule_browser_control_recovery_phase6d" else "FAIL",
        f"id={cid}",
    )
    trace = c.get("execution_trace") or []
    _record(
        results,
        "18.capsule_execution_trace_length_ge_4",
        "PASS" if len(trace) >= 4 else "FAIL",
        f"len={len(trace)}",
    )
    canary_step = next((s for s in trace if s.get("stage") == "canary"), None)
    if not canary_step:
        _record(results, "19.capsule_canary_step_present", "FAIL", "no canary step")
    else:
        result = canary_step.get("result") or {}
        must = ["no_hub", "no_publish", "no_approve", "no_solidify",
                "no_real_browser_launch", "no_port_connection", "no_http_request",
                "no_curl_wget", "no_env_scan", "no_secret_echo"]
        missing = [k for k in must if result.get(k) is not True]
        _record(
            results,
            "19.capsule_canary_step_present",
            "PASS" if not missing else "FAIL",
            f"missing={missing}" if missing else "ok",
        )


def check_bundle(results):
    if not BUNDLE.exists():
        _record(results, "20.bundle_exists", "FAIL", str(BUNDLE))
        return
    try:
        b = _read_json(BUNDLE)
    except Exception as e:
        _record(results, "20.bundle_json", "FAIL", f"parse_error: {e}")
        return
    _record(results, "20.bundle_exists", "PASS")
    _record(
        results,
        "21.bundle_schema_version",
        "PASS" if b.get("schema_version") == "atl-evomap-portable-bundle-v0.1" else "FAIL",
        f"schema_version={b.get('schema_version')}",
    )
    _record(
        results,
        "22.bundle_source_phase",
        "PASS" if b.get("source_phase") == "ATL-EVOMAP-6D" else "FAIL",
        f"source_phase={b.get('source_phase')}",
    )
    safety = b.get("safety", {})
    safety_ok = (
        safety.get("hub") == "disabled"
        and safety.get("publish") == "disabled"
        and safety.get("credits") == 0
        and safety.get("visibility") == "private"
        and safety.get("no_secrets") is True
        and safety.get("no_real_browser_launch") is True
        and safety.get("no_port_connection") is True
    )
    _record(
        results,
        "23.bundle_safety_ok",
        "PASS" if safety_ok else "FAIL",
        f"safety={safety}",
    )


def check_inspect_validate(results):
    if not INSPECT.exists():
        _record(results, "24.inspect_output_exists", "FAIL", str(INSPECT))
    else:
        try:
            data = _read_json(INSPECT)
            _record(
                results,
                "24.inspect_output_ok_true",
                "PASS" if data.get("ok") else "FAIL",
                f"ok={data.get('ok')}",
            )
        except Exception as e:
            _record(results, "24.inspect_output_json", "FAIL", f"parse_error: {e}")

    if not VALIDATE.exists():
        _record(results, "25.validate_output_exists", "FAIL", str(VALIDATE))
    else:
        try:
            data = _read_json(VALIDATE)
            ok = data.get("ok")
            secret_hits = data.get("secret_hits") or []
            _record(
                results,
                "25.validate_output_ok_and_no_secrets",
                "PASS" if (ok is True and len(secret_hits) == 0) else "FAIL",
                f"ok={ok} secret_hits={len(secret_hits)}",
            )
        except Exception as e:
            _record(results, "25.validate_output_json", "FAIL", f"parse_error: {e}")


def check_apply(results):
    if not APPLY_DRY.exists():
        _record(results, "26.apply_dry_run_exists", "FAIL", str(APPLY_DRY))
    else:
        try:
            data = _read_json(APPLY_DRY)
            _record(
                results,
                "26.apply_dry_run_ok_true",
                "PASS" if data.get("ok") else "FAIL",
                f"ok={data.get('ok')}",
            )
        except Exception as e:
            _record(results, "26.apply_dry_run_json", "FAIL", f"parse_error: {e}")

    if not APPLY_YES.exists():
        _record(results, "27.apply_yes_exists", "FAIL", str(APPLY_YES))
    else:
        try:
            data = _read_json(APPLY_YES)
            _record(
                results,
                "27.apply_yes_ok_true",
                "PASS" if data.get("ok") else "FAIL",
                f"ok={data.get('ok')}",
            )
        except Exception as e:
            _record(results, "27.apply_yes_json", "FAIL", f"parse_error: {e}")

    if not APPLY_SUMMARY.exists():
        _record(results, "28.apply_target_summary_exists", "FAIL", str(APPLY_SUMMARY))
        return
    try:
        s = _read_json(APPLY_SUMMARY)
    except Exception as e:
        _record(results, "28.apply_target_summary_json", "FAIL", f"parse_error: {e}")
        return
    gene_count = s.get("gene_count", 0)
    capsule_count = s.get("capsule_count", 0)
    _record(
        results,
        "28.apply_target_gene_and_capsule_present",
        "PASS" if gene_count >= 1 and capsule_count >= 1 else "FAIL",
        f"gene_count={gene_count} capsule_count={capsule_count}",
    )
    signals = set(s.get("signals", []))
    missing = REQUIRED_TARGET_SIGNALS - signals
    _record(
        results,
        "29.apply_target_required_signals",
        "PASS" if not missing else "FAIL",
        f"missing={sorted(missing)}" if missing else f"signals_count={len(signals)}",
    )


def check_manifest_and_smoke(results):
    if not MANIFEST.exists():
        _record(results, "30.nightly_manifest_exists", "FAIL", str(MANIFEST))
        return
    try:
        m = _read_json(MANIFEST)
    except Exception as e:
        _record(results, "30.nightly_manifest_json", "FAIL", f"parse_error: {e}")
        return
    bundles = m.get("bundles", [])
    has_6d = any(
        isinstance(b, str) and b.endswith("browser-control-recovery.bundle.json")
        for b in bundles
    ) or any(
        isinstance(b, dict) and b.get("path", "").endswith("browser-control-recovery.bundle.json")
        for b in bundles
    )
    _record(
        results,
        "30.nightly_manifest_has_6d",
        "PASS" if has_6d else "FAIL",
        f"bundles_count={len(bundles)} has_6d={has_6d}",
    )
    _record(
        results,
        "31.nightly_manifest_extended_by_phase",
        "PASS" if m.get("extended_by_phase") == "ATL-EVOMAP-6D" else "FAIL",
        f"extended_by_phase={m.get('extended_by_phase')}",
    )

    if not SMOKE_DIGEST.exists():
        _record(results, "32.smoke_digest_exists", "FAIL", str(SMOKE_DIGEST))
        return
    try:
        d = _read_json(SMOKE_DIGEST)
    except Exception as e:
        _record(results, "32.smoke_digest_json", "FAIL", f"parse_error: {e}")
        return

    overall = d.get("overall_status")
    _record(
        results,
        "32.smoke_digest_overall_pass",
        "PASS" if overall == "PASS" else "FAIL",
        f"overall_status={overall}",
    )
    bi = len(d.get("bundle_checks", {}).get("inspect", []))
    bv = len(d.get("bundle_checks", {}).get("validate", []))
    _record(
        results,
        "33.smoke_digest_bundle_counts_5_5",
        "PASS" if bi == 5 and bv == 5 else "FAIL",
        f"inspect={bi} validate={bv}",
    )
    canary_status = (d.get("canary_summary", {}) or {}).get("status")
    _record(
        results,
        "34.smoke_digest_canary_pass",
        "PASS" if canary_status == "CANARY_PASS" else "FAIL",
        f"canary_status={canary_status}",
    )
    # secret scan row
    secret_row = next((c for c in d.get("checks", []) if c.get("check_id") == "secret_scan_clean"), None)
    if secret_row:
        hits = 0
        try:
            hits = sum(len(v) for v in (secret_row.get("extra", {}) or {}).get("hits", {}).values() if isinstance(v, list))
        except Exception:
            hits = -1
        _record(
            results,
            "35.smoke_digest_secret_scan_clean",
            "PASS" if secret_row.get("status") == "PASS" and hits == 0 else "FAIL",
            f"status={secret_row.get('status')} hits={hits}",
        )
    # git hygiene
    git_row = next((c for c in d.get("checks", []) if c.get("check_id") == "git_hygiene_no_root_evolver_or_memory"), None)
    if git_row:
        _record(
            results,
            "36.smoke_digest_git_hygiene_ok",
            "PASS" if git_row.get("status") == "PASS" else "FAIL",
            f"status={git_row.get('status')}",
        )
    # hard boundaries
    hb = d.get("hard_boundaries", {})
    _record(
        results,
        "37.smoke_digest_hard_boundaries_ok",
        "PASS" if bool(hb) and all(hb.values()) else "FAIL",
        f"fields={len(hb)}",
    )


def check_reports_and_readmes(results):
    if not CASE_README.exists():
        _record(results, "38.case_readme_exists", "FAIL", str(CASE_README))
    else:
        _record(results, "38.case_readme_exists", "PASS")

    if not CASE_REPORT.exists():
        _record(results, "39.case_report_exists", "FAIL", str(CASE_REPORT))
    else:
        _record(results, "39.case_report_exists", "PASS")

    if not TOP_REPORT.exists():
        _record(results, "40.top_report_exists", "FAIL", str(TOP_REPORT))
    else:
        _record(results, "40.top_report_exists", "PASS")

    if not MAIN_README.exists():
        _record(results, "41.main_readme_exists", "FAIL", str(MAIN_README))
    else:
        text = MAIN_README.read_text(encoding="utf-8")
        _record(
            results,
            "41.main_readme_mentions_6d",
            "PASS" if "ATL-EVOMAP-6D" in text else "FAIL",
            f"length={len(text)}",
        )


def check_cases_json_and_git(results):
    cases_json = REPO_ROOT / "data" / "cases.json"
    if not cases_json.exists():
        _record(results, "42.cases_json_exists", "FAIL", str(cases_json))
    else:
        try:
            d = _read_json(cases_json)
            text = json.dumps(d, ensure_ascii=False)
            _record(
                results,
                "42.cases_json_has_6d",
                "PASS" if "ATL-EVOMAP-6D" in text else "FAIL",
                "ok",
            )
        except Exception as e:
            _record(results, "42.cases_json_json", "FAIL", f"parse_error: {e}")

    # git status: no root .evolver/ or memory/ tracked
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        tracked = proc.stdout.splitlines()
        bad = [
            p for p in tracked
            if p == ".evolver" or p.startswith(".evolver/")
            or p == "memory" or p.startswith("memory/")
        ]
        _record(
            results,
            "43.git_no_root_evolver_or_memory",
            "PASS" if not bad else "FAIL",
            f"violations={bad[:5]}",
        )
    except Exception as e:
        _record(results, "43.git_no_root_evolver_or_memory", "FAIL", f"error: {e}")


def check_prior_validators(results):
    """Run all 9 prior validators in-process.  We spawn python3 directly."""
    for i, name in enumerate(PRIOR_VALIDATORS, start=44):
        path = REPO_ROOT / "scripts" / name
        if not path.exists():
            _record(results, f"{i}.prior.{name}", "FAIL", "missing")
            continue
        try:
            proc = subprocess.run(
                ["python3", str(path)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=900,
            )
            # Convention: validators print either "ALL CHECKS PASSED" or
            # "FAIL  SOME CHECKS FAILED" or a "FAILED checks:" block.
            # We treat rc == 0 AND "FAIL" not in the last 200 chars of
            # stdout as PASS; otherwise FAIL.
            tail = (proc.stdout or "")[-400:]
            ok = (proc.returncode == 0) and ("FAIL" not in tail)
            _record(
                results,
                f"{i}.prior.{name}",
                "PASS" if ok else "FAIL",
                f"rc={proc.returncode}",
            )
        except Exception as e:
            _record(results, f"{i}.prior.{name}", "FAIL", f"error: {e}")


def main() -> int:
    results: list[dict] = []
    check_parser_and_fixture(results)
    check_parser_selftests(results)
    check_gene(results)
    check_capsule(results)
    check_bundle(results)
    check_inspect_validate(results)
    check_apply(results)
    check_manifest_and_smoke(results)
    check_reports_and_readmes(results)
    check_cases_json_and_git(results)
    check_prior_validators(results)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print("=" * 72)
    print(f"ATL-EVOMAP-6D validator — {passed} PASS, {failed} FAIL")
    print("=" * 72)
    for r in results:
        marker = "\033[32m[PASS]\033[0m" if r["status"] == "PASS" else "\033[91m[FAIL]\033[0m"
        print(f"  {marker} {r['check_id']} — {r['detail']}")
    print("=" * 72)
    print(f"TOTAL: {len(results)} checks; PASS={passed} FAIL={failed}")
    if failed:
        print("RESULT: SOME CHECKS FAILED")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
