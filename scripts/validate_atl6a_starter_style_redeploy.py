#!/usr/bin/env python3
"""ATL-6A starter-style redeploy validator (Python stdlib only)."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REDEPLOY_DIR = (
    REPO_ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "starter-style-redeploy"
)

ENV_FILE = REDEPLOY_DIR / "environment_starter_style.py"
REWARD_FILE = REDEPLOY_DIR / "reward_starter_style.py"
SUBSET_FILE = REDEPLOY_DIR / "prepare_starter_style_subset.py"
VALIDATE_FILE = REDEPLOY_DIR / "validate_starter_style_env.py"
REDEPLOY_SCRIPT = REDEPLOY_DIR / "atl6_starter_style_redeploy.py"
TRAIN_FILE = REDEPLOY_DIR / "starter-train.preview.jsonl"
EVAL_FILE = REDEPLOY_DIR / "starter-eval.preview.jsonl"

OLD_FAILED_RUN_ID = "c83f971d-2b2c-42b8-9774-ca64938c1286"
NEW_RUN_NAME = "hermes-phase-closer-smoke-atl6a"
ATL6A_AUTH = "I AUTHORIZE ATL-6A STARTER-STYLE REDEPLOY"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"sk_test_[A-Za-z0-9]{8,}"),
    re.compile(r"cf_[A-Za-z0-9]{8,}"),
    re.compile(r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9]{8,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE),
    re.compile(r"Cookie\s*:\s*[A-Za-z0-9=._;-]{8,}", re.IGNORECASE),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"gho_[A-Za-z0-9]{16,}"),
    re.compile(r"ghu_[A-Za-z0-9]{16,}"),
    re.compile(r"ghs_[A-Za-z0-9]{16,}"),
    re.compile(r"ghr_[A-Za-z0-9]{16,}"),
]


def _scan_secrets(path):
    issues = []
    if not path.exists():
        return issues
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unreadable {path.name}: {exc}"]
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            issues.append(
                f"{path.name}: secret-shaped match for pattern {pat.pattern!r}: <REDACTED_SECRET_LITERAL>"
            )
    return issues


def _check_file_exists(path):
    if not path.exists():
        return [f"missing file: {path.name}"]
    return []


def _check_env_class(path):
    issues = []
    if not path.exists():
        return issues
    text = path.read_text(encoding="utf-8")
    if "class HermesPhaseCloserStarterStyleEnv" not in text:
        issues.append(f"{path.name}: missing class HermesPhaseCloserStarterStyleEnv")
    if "BaseEnv" not in text:
        issues.append(f"{path.name}: does not import BaseEnv")
    if re.search(r"def\s+run_tool\s*\(", text) and re.search(r"return\s+\"\"\s*", text, re.MULTILINE):
        pass
    else:
        issues.append(f"{path.name}: run_tool does not return empty string (no-tools contract)")
    if re.search(r"def\s+load_dataset\s*\(", text):
        issues.append(f"{path.name}: defines a custom load_dataset override (ATL-6A fix point: avoid override)")
    return issues


def _check_reward(path):
    issues = []
    if not path.exists():
        return issues
    text = path.read_text(encoding="utf-8")
    if "def score_completion" not in text:
        issues.append(f"{path.name}: missing score_completion")
    if not re.search(r"min\(\s*1\.0", text) and "clamp" not in text.lower():
        issues.append(f"{path.name}: no obvious 0.0~1.0 clamp")
    return issues


def _check_redeploy_script(path):
    issues = []
    if not path.exists():
        return issues
    text = path.read_text(encoding="utf-8")
    if NEW_RUN_NAME not in text:
        issues.append(f"{path.name}: missing run_name {NEW_RUN_NAME!r}")
    if ATL6A_AUTH not in text:
        issues.append(f"{path.name}: missing authorization literal {ATL6A_AUTH!r}")
    if OLD_FAILED_RUN_ID in text:
        issues.append(f"{path.name}: references old failed run_id {OLD_FAILED_RUN_ID}")
    if "TRAIN_SAMPLES = 16" not in text:
        issues.append(f"{path.name}: TRAIN_SAMPLES != 16")
    if "EVAL_SAMPLES = 4" not in text:
        issues.append(f"{path.name}: EVAL_SAMPLES != 4")
    batch_size_pat = r'"batch_size"\s*:'
    if re.search(batch_size_pat, text):
        issues.append(f"{path.name}: launcher_args contains batch_size")
    return issues


def _check_dataset(path, expected):
    issues = []
    if not path.exists():
        issues.append(f"missing dataset: {path.name}")
        return issues
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
    if n != expected:
        issues.append(f"{path.name}: expected {expected} rows, got {n}")
    return issues


def _check_python_syntax(path):
    if not path.exists():
        return []
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path.name}: SyntaxError: {exc}"]
    return []


def main():
    issues = []

    if not REDEPLOY_DIR.exists():
        issues.append(f"missing redeploy directory: {REDEPLOY_DIR}")
    if REDEPLOY_DIR.exists() and not REDEPLOY_DIR.is_dir():
        issues.append(f"redeploy path is not a directory: {REDEPLOY_DIR}")

    for path in (ENV_FILE, REWARD_FILE, SUBSET_FILE, VALIDATE_FILE, REDEPLOY_SCRIPT):
        issues.extend(_check_file_exists(path))
        issues.extend(_check_python_syntax(path))

    issues.extend(_check_env_class(ENV_FILE))
    issues.extend(_check_reward(REWARD_FILE))
    issues.extend(_check_redeploy_script(REDEPLOY_SCRIPT))

    issues.extend(_check_dataset(TRAIN_FILE, 16))
    issues.extend(_check_dataset(EVAL_FILE, 4))

    for path in (ENV_FILE, REWARD_FILE, REDEPLOY_SCRIPT, VALIDATE_FILE):
        issues.extend(_scan_secrets(path))

    if issues:
        print("FAIL: validate_atl6a_starter_style_redeploy")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS: validate_atl6a_starter_style_redeploy")
    print(f"  - redeploy dir: {REDEPLOY_DIR}")
    print("  - env class: HermesPhaseCloserStarterStyleEnv (no-tools, no load_dataset override)")
    print("  - reward: 0.0~1.0 format/coverage/score")
    print("  - dataset: 16 train / 4 eval preview")
    print(f"  - redeploy run_name: {NEW_RUN_NAME}")
    print(f"  - old failed run {OLD_FAILED_RUN_ID[:8]}... NOT referenced")
    print(f"  - secret-pattern scan: clean ({len(SECRET_PATTERNS)} patterns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
