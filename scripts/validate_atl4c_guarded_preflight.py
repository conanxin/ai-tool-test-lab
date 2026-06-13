#!/usr/bin/env python3
"""
ATL-4C validator: validate_atl4c_guarded_preflight.py

Validates the Castform guarded cloud smoke preflight configuration.

Checks:
- guarded-cloud-preflight/ directory exists.
- guarded_cloud_preflight_config.json parses and contains required fields.
- cloud_launch_allowed is false.
- current_readiness is BLOCKED_BY_UNCLEAR_CHARGES.
- actual_upload_allowed_in_this_phase is false.
- actual_launch_allowed_in_this_phase is false.
- README.md, API_KEY_RUNTIME_ONLY.md, FINAL_LAUNCH_GATE.md exist.
- guarded_upload_preflight.py and guarded_launch_preflight.py exist.
- guarded_upload_preflight.py refuses upload (exit 1, banner).
- guarded_launch_preflight.py refuses launch (exit 1, banner).
- No real secret-shaped strings inside guarded-cloud-preflight/ artifacts.
- No forbidden executable calls (upload_training_run, launch_training_run,
  TrainerClient) inside the Python scripts (string mentions in docs are OK).
- Does not modify any file.

Exits 0 on PASS, non-zero on FAIL. Std-lib only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "cases" / "castform-hermes-phase-closer-v0"
PREFLIGHT_DIR = CASE_DIR / "guarded-cloud-preflight"

REQUIRED_FILES = [
    "guarded_cloud_preflight_config.json",
    "README.md",
    "API_KEY_RUNTIME_ONLY.md",
    "FINAL_LAUNCH_GATE.md",
    "guarded_upload_preflight.py",
    "guarded_launch_preflight.py",
]

REQUIRED_CONFIG_FIELDS = [
    "phase",
    "run_name",
    "base_model",
    "selected_path",
    "train_preview_file",
    "eval_preview_file",
    "train_sample_count",
    "eval_sample_count",
    "cloud_launch_allowed",
    "current_readiness",
    "user_declared_readiness",
    "risk_note",
    "requires_env_var_castform_api_key",
    "requires_env_var_atl_allow_upload",
    "requires_env_var_atl_allow_launch",
    "actual_upload_allowed_in_this_phase",
    "actual_launch_allowed_in_this_phase",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
]

KEY_ASSIGN_RE = re.compile(
    r"""(?ix)
    \b(?:CASTFORM_API_KEY|castform_api_key|api_key|token|secret|password)\b
    \s*=\s*
    ['"](?P<v>[^'"\<\>\s]{16,})['"]
    """
)

FORBIDDEN_CALL_PATTERNS = [
    re.compile(r"\bupload_training_run\s*\("),
    re.compile(r"\blaunch_training_run\s*\("),
    re.compile(r"\bTrainerClient\s*\("),
    re.compile(r"from\s+castform[^\n]*import[^\n]*(?:upload_training_run|launch_training_run|TrainerClient)"),
    re.compile(r"import\s+castform[^\n]*(?:upload_training_run|launch_training_run|TrainerClient)"),
]


class V:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checks: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        self.checks.append(f"[FAIL] {msg}")

    def ok(self, msg: str) -> None:
        self.checks.append(f"[OK]   {msg}")


def check_files_exist(v: V) -> None:
    if not PREFLIGHT_DIR.is_dir():
        v.fail(f"missing directory: {PREFLIGHT_DIR}")
        return
    v.ok(f"directory exists: {PREFLIGHT_DIR}")
    for name in REQUIRED_FILES:
        p = PREFLIGHT_DIR / name
        if not p.exists():
            v.fail(f"missing required file: {p.relative_to(ROOT)}")
        else:
            v.ok(f"file exists: {p.relative_to(ROOT)}")


def check_config_json(v: V) -> dict | None:
    cfg_path = PREFLIGHT_DIR / "guarded_cloud_preflight_config.json"
    if not cfg_path.exists():
        return None
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        v.fail(f"guarded_cloud_preflight_config.json is not valid JSON: {exc}")
        return None
    v.ok("guarded_cloud_preflight_config.json parses as JSON")

    for field in REQUIRED_CONFIG_FIELDS:
        if field not in cfg:
            v.fail(f"guarded_cloud_preflight_config.json missing required field: {field}")
        else:
            v.ok(f"guarded_cloud_preflight_config.json has field: {field}")

    if cfg.get("cloud_launch_allowed") is not False:
        v.fail(f"cloud_launch_allowed must be false, got {cfg.get('cloud_launch_allowed')!r}")
    else:
        v.ok("cloud_launch_allowed == false")

    if cfg.get("current_readiness") != "BLOCKED_BY_UNCLEAR_CHARGES":
        v.fail(
            f"current_readiness must be BLOCKED_BY_UNCLEAR_CHARGES, "
            f"got {cfg.get('current_readiness')!r}"
        )
    else:
        v.ok("current_readiness == BLOCKED_BY_UNCLEAR_CHARGES")

    if cfg.get("actual_upload_allowed_in_this_phase") is not False:
        v.fail(
            f"actual_upload_allowed_in_this_phase must be false, "
            f"got {cfg.get('actual_upload_allowed_in_this_phase')!r}"
        )
    else:
        v.ok("actual_upload_allowed_in_this_phase == false")

    if cfg.get("actual_launch_allowed_in_this_phase") is not False:
        v.fail(
            f"actual_launch_allowed_in_this_phase must be false, "
            f"got {cfg.get('actual_launch_allowed_in_this_phase')!r}"
        )
    else:
        v.ok("actual_launch_allowed_in_this_phase == false")

    if cfg.get("phase") != "ATL-4C":
        v.fail(f"phase must be ATL-4C, got {cfg.get('phase')!r}")
    else:
        v.ok("phase == ATL-4C")

    if cfg.get("run_name") != "hermes-phase-closer-smoke":
        v.fail(f"run_name mismatch: {cfg.get('run_name')!r}")
    else:
        v.ok("run_name == hermes-phase-closer-smoke")

    if cfg.get("base_model") != "Qwen/Qwen3.5-4B":
        v.fail(f"base_model mismatch: {cfg.get('base_model')!r}")
    else:
        v.ok("base_model == Qwen/Qwen3.5-4B")

    if cfg.get("train_sample_count") != 8:
        v.fail(f"train_sample_count must be 8, got {cfg.get('train_sample_count')!r}")
    else:
        v.ok("train_sample_count == 8")
    if cfg.get("eval_sample_count") != 2:
        v.fail(f"eval_sample_count must be 2, got {cfg.get('eval_sample_count')!r}")
    else:
        v.ok("eval_sample_count == 2")

    return cfg


def scan_for_secrets(v: V) -> None:
    if not PREFLIGHT_DIR.is_dir():
        return
    for p in PREFLIGHT_DIR.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".zip"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                v.fail(f"forbidden secret-shaped string in {p.relative_to(ROOT)}: pattern {pat.pattern}")
        for m in KEY_ASSIGN_RE.finditer(text):
            v.fail(
                f"key-like assignment in {p.relative_to(ROOT)}: "
                f"variable assigned {m.group('v')[:4]}... (redacted)"
            )


def check_python_scripts_clean(v: V) -> None:
    if not PREFLIGHT_DIR.is_dir():
        return
    for p in PREFLIGHT_DIR.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix != ".py":
            continue
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT)
        for pat in FORBIDDEN_CALL_PATTERNS:
            if pat.search(text):
                v.fail(f"forbidden executable pattern {pat.pattern!r} in {rel}")
            else:
                v.ok(f"clean: {rel} (no {pat.pattern!r})")


def check_guard_refuses(v: V, script_name: str, banner_needles: tuple[str, ...]) -> None:
    guard = PREFLIGHT_DIR / script_name
    if not guard.exists():
        v.fail(f"{script_name} missing; cannot verify refusal behavior")
        return
    proc = subprocess.run(
        [sys.executable, str(guard)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode == 0:
        v.fail(f"{script_name} exited 0 — guard must refuse by default")
    else:
        v.ok(f"{script_name} refused (exit {proc.returncode})")
    for needle in banner_needles:
        if needle in proc.stdout:
            v.ok(f"{script_name} banner contains: {needle!r}")
        else:
            v.fail(f"{script_name} banner missing: {needle!r}")


def main() -> int:
    v = V()
    check_files_exist(v)
    check_config_json(v)
    scan_for_secrets(v)
    check_python_scripts_clean(v)
    check_guard_refuses(
        v,
        "guarded_upload_preflight.py",
        (
            "ATL-4C guarded upload preflight",
            "actual_upload_allowed_in_this_phase=false",
            "BLOCKED_BY_UNCLEAR_CHARGES",
            "no API call",
            "no upload",
            "no training",
        ),
    )
    check_guard_refuses(
        v,
        "guarded_launch_preflight.py",
        (
            "ATL-4C guarded launch preflight",
            "actual_launch_allowed_in_this_phase=false",
            "BLOCKED_BY_UNCLEAR_CHARGES",
            "no API call",
            "no upload",
            "no training",
        ),
    )

    print("=" * 60)
    print("ATL-4C validator")
    print("=" * 60)
    for line in v.checks:
        print(line)
    print()
    if v.errors:
        print(f"RESULT: FAIL ({len(v.errors)} error(s))")
        for e in v.errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
