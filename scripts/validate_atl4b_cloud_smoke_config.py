#!/usr/bin/env python3
"""
ATL-4B-CONFIG validator: validate_atl4b_cloud_smoke_config.py

Validates the Castform cloud smoke run dry configuration.

Checks:
- cloud-smoke-run/ directory exists.
- cloud_smoke_config.json parses and contains the required fields.
- cloud_launch_allowed is false.
- current_readiness is BLOCKED_BY_UNCLEAR_CHARGES.
- README.md, API_KEY_HANDLING.md, COST_GUARD.md exist.
- prepare_cloud_smoke_subset.py and cloud_launch_guard.py exist.
- preview files exist with correct row counts (8 train, 2 eval).
- No real secret-shaped strings inside the cloud-smoke-run/ artifacts.
- No forbidden executable calls (upload_training_run, launch_training_run,
  TrainerClient) inside the Python scripts (string mentions in docs are OK).

Exits 0 on PASS, non-zero on FAIL. Std-lib only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "cases" / "castform-hermes-phase-closer-v0"
SMOKE_DIR = CASE_DIR / "cloud-smoke-run"

REQUIRED_FILES = [
    "cloud_smoke_config.json",
    "README.md",
    "API_KEY_HANDLING.md",
    "COST_GUARD.md",
    "prepare_cloud_smoke_subset.py",
    "cloud_launch_guard.py",
    "smoke-train.preview.jsonl",
    "smoke-eval.preview.jsonl",
]

REQUIRED_CONFIG_FIELDS = [
    "phase",
    "run_name",
    "template_path",
    "base_model",
    "train_sample_count",
    "eval_sample_count",
    "dataset_source",
    "environment_source",
    "reward_source",
    "tools",
    "external_network_tools",
    "cloud_launch_allowed",
    "requires_user_credit_billing_confirmation",
    "requires_explicit_user_api_key_authorization",
    "current_readiness",
]

# Patterns that look like real secrets — must NOT appear in this dir.
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"cf-[A-Za-z0-9]{20,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
]

# Looks like a real key assigned to a key-like variable.
KEY_ASSIGN_RE = re.compile(
    r"""(?ix)
    \b(?:CASTFORM_API_KEY|castform_api_key|api_key|token|secret|password)\b
    \s*=\s*
    ['"](?P<v>[^'"<>\s]{16,})['"]
    """
)

FORBIDDEN_CALL_PATTERNS = [
    re.compile(r"\bupload_training_run\s*\("),
    re.compile(r"\blaunch_training_run\s*\("),
    re.compile(r"\bTrainerClient\s*\("),
    re.compile(r"from\s+castform[^\\n]*import[^\\n]*(?:upload_training_run|launch_training_run|TrainerClient)"),
    re.compile(r"import\s+castform[^\\n]*(?:upload_training_run|launch_training_run|TrainerClient)"),
]

# Allowed in docs as plain English — but still scanned for executable form.
PY_SCRIPT_GLOBS = ("*.py",)


class V:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        self.checks.append(f"[FAIL] {msg}")

    def ok(self, msg: str) -> None:
        self.checks.append(f"[OK]   {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        self.checks.append(f"[WARN] {msg}")


def check_files_exist(v: V) -> None:
    if not SMOKE_DIR.is_dir():
        v.fail(f"missing directory: {SMOKE_DIR}")
        return
    v.ok(f"directory exists: {SMOKE_DIR}")
    for name in REQUIRED_FILES:
        p = SMOKE_DIR / name
        if not p.exists():
            v.fail(f"missing required file: {p.relative_to(ROOT)}")
        else:
            v.ok(f"file exists: {p.relative_to(ROOT)}")


def check_config_json(v: V) -> dict | None:
    cfg_path = SMOKE_DIR / "cloud_smoke_config.json"
    if not cfg_path.exists():
        return None
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        v.fail(f"cloud_smoke_config.json is not valid JSON: {exc}")
        return None
    v.ok("cloud_smoke_config.json parses as JSON")

    for field in REQUIRED_CONFIG_FIELDS:
        if field not in cfg:
            v.fail(f"cloud_smoke_config.json missing required field: {field}")
        else:
            v.ok(f"cloud_smoke_config.json has field: {field}")

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

    if cfg.get("phase") != "ATL-4B-CONFIG":
        v.fail(f"phase must be ATL-4B-CONFIG, got {cfg.get('phase')!r}")
    else:
        v.ok("phase == ATL-4B-CONFIG")

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


def check_preview_row_counts(v: V) -> None:
    for name, expected in (("smoke-train.preview.jsonl", 8), ("smoke-eval.preview.jsonl", 2)):
        p = SMOKE_DIR / name
        if not p.exists():
            continue
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) != expected:
            v.fail(f"{name} expected {expected} rows, got {len(lines)}")
        else:
            v.ok(f"{name} has {expected} rows")


def scan_for_secrets(v: V) -> None:
    if not SMOKE_DIR.is_dir():
        return
    for p in SMOKE_DIR.rglob("*"):
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
    if not SMOKE_DIR.is_dir():
        return
    for p in SMOKE_DIR.rglob("*"):
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


def check_guard_refuses(v: V) -> None:
    """Re-execute cloud_launch_guard.py and require it to exit non-zero
    with the blocked banner."""
    import subprocess

    guard = SMOKE_DIR / "cloud_launch_guard.py"
    if not guard.exists():
        v.fail("cloud_launch_guard.py missing; cannot verify refusal behavior")
        return
    proc = subprocess.run(
        [sys.executable, str(guard)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode == 0:
        v.fail("cloud_launch_guard.py exited 0 — guard must refuse launch by default")
    else:
        v.ok(f"cloud_launch_guard.py refused launch (exit {proc.returncode})")
    for needle in (
        "ATL-4B-CONFIG dry configuration only",
        "cloud_launch_allowed=false",
        "BLOCKED_BY_UNCLEAR_CHARGES",
        "no API call",
        "no upload",
        "no training",
    ):
        if needle in proc.stdout:
            v.ok(f"guard banner contains: {needle!r}")
        else:
            v.fail(f"guard banner missing: {needle!r}")


def main() -> int:
    v = V()
    check_files_exist(v)
    check_config_json(v)
    check_preview_row_counts(v)
    scan_for_secrets(v)
    check_python_scripts_clean(v)
    check_guard_refuses(v)

    print("=" * 60)
    print("ATL-4B-CONFIG validator")
    print("=" * 60)
    for line in v.checks:
        print(line)
    if v.warnings:
        print()
        print("WARNINGS:")
        for w in v.warnings:
            print(f"  - {w}")
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
