#!/usr/bin/env python3
"""ATL-6 starter-style redeploy validator (Python stdlib only)."""

from __future__ import annotations

import json
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
TRAIN_FILE = REDEPLOY_DIR / "starter-train.preview.jsonl"
EVAL_FILE = REDEPLOY_DIR / "starter-eval.preview.jsonl"
ENV_FILE = REDEPLOY_DIR / "environment_starter_style.py"
REWARD_FILE = REDEPLOY_DIR / "reward_starter_style.py"
REDEPLOY_SCRIPT = REDEPLOY_DIR / "atl6_starter_style_redeploy.py"
RESULT_FILE = REDEPLOY_DIR / "atl6_starter_style_redeploy_result.json"

EXPECTED_TRAIN = 16
EXPECTED_EVAL = 4
EXPECTED_RESULT_TRAIN = 16
EXPECTED_RESULT_EVAL = 4
EXPECTED_URL_HOST = "app.castform.com"

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9_-]{4,}"),
    re.compile(r"Authorization\s*:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"Cookie\s*:\s*\S+", re.IGNORECASE),
    re.compile(r"cf_[A-Za-z0-9]{8,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*[A-Za-z0-9]{16,}", re.IGNORECASE),
)


def _count_jsonl_rows(path):
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
    return n


def _check_redeploy_dir():
    issues = []
    if not REDEPLOY_DIR.exists():
        issues.append("missing starter-style-redeploy directory")
    elif not REDEPLOY_DIR.is_dir():
        issues.append("starter-style-redeploy path is not a directory")
    return issues


def _check_dataset_sizes():
    issues = []
    for path, expected in (
        (TRAIN_FILE, EXPECTED_TRAIN),
        (EVAL_FILE, EXPECTED_EVAL),
    ):
        if not path.exists():
            issues.append(f"missing dataset: {path.name}")
            continue
        n = _count_jsonl_rows(path)
        if n != expected:
            issues.append(f"{path.name}: expected {expected} rows, got {n}")
    return issues


def _check_environment():
    issues = []
    if not ENV_FILE.exists():
        issues.append("missing environment_starter_style.py")
        return issues
    text = ENV_FILE.read_text(encoding="utf-8")
    if "class HermesPhaseCloserStarterStyleEnv" not in text:
        issues.append("environment_starter_style.py: missing class HermesPhaseCloserStarterStyleEnv")
    # run_tool must not raise NotImplementedError. Find run_tool body.
    m = re.search(
        r"async def run_tool\s*\(.*?(?=\n    (async def|def |class |@))",
        text,
        re.DOTALL,
    )
    if m and "raise NotImplementedError" in m.group(0):
        issues.append("environment_starter_style.py: run_tool still raises NotImplementedError")
    if m and "return" not in m.group(0):
        issues.append("environment_starter_style.py: run_tool does not return (must return empty string)")
    return issues


def _check_reward():
    issues = []
    if not REWARD_FILE.exists():
        issues.append("missing reward_starter_style.py")
        return issues
    text = REWARD_FILE.read_text(encoding="utf-8")
    if "def score_completion" not in text:
        issues.append("reward_starter_style.py: missing score_completion")
    if not re.search(r"0\.0", text):
        issues.append("reward_starter_style.py: no 0.0 constant found")
    if not re.search(r"1\.0", text):
        issues.append("reward_starter_style.py: no 1.0 constant found")
    if not re.search(r"min\(\s*1\.0", text):
        issues.append("reward_starter_style.py: no min(1.0, ...) clamp to [0.0, 1.0]")
    return issues


def _check_redeploy_script():
    issues = []
    if not REDEPLOY_SCRIPT.exists():
        issues.append("missing atl6_starter_style_redeploy.py")
        return issues
    text = REDEPLOY_SCRIPT.read_text(encoding="utf-8")
    if re.search(r"batch_size", text):
        issues.append("atl6_starter_style_redeploy.py: contains batch_size (must be removed)")
    if not re.search(r"learning_rate", text):
        issues.append("atl6_starter_style_redeploy.py: missing learning_rate in launcher_args")
    return issues


def _check_result_json():
    issues = []
    if not RESULT_FILE.exists():
        return issues, "SKIPPED_RESULT_NOT_PRESENT"
    try:
        text = RESULT_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"result JSON unreadable: {exc}")
        return issues, None
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            issues.append(
                f"result JSON: secret-shaped match for pattern {pat.pattern!r}: <REDACTED_SECRET_LITERAL>"
            )
    if data.get("train_samples") != EXPECTED_RESULT_TRAIN:
        issues.append(f"result JSON: train_samples != {EXPECTED_RESULT_TRAIN}")
    if data.get("eval_samples") != EXPECTED_RESULT_EVAL:
        issues.append(f"result JSON: eval_samples != {EXPECTED_RESULT_EVAL}")
    if data.get("launch_succeeded") is True:
        run_id = data.get("run_id")
        if not run_id or not str(run_id).strip():
            issues.append("result JSON: launch_succeeded=true but run_id is empty")
        url = data.get("experiment_url") or ""
        if EXPECTED_URL_HOST not in url:
            issues.append(f"result JSON: experiment_url does not contain {EXPECTED_URL_HOST!r}")
    return issues, None


def main():
    issues = []
    issues.extend(_check_redeploy_dir())
    issues.extend(_check_dataset_sizes())
    issues.extend(_check_environment())
    issues.extend(_check_reward())
    issues.extend(_check_redeploy_script())
    result_issues, skip_status = _check_result_json()
    issues.extend(result_issues)
    if issues:
        print("FAIL: validate_atl6_starter_style_redeploy")
        for line in issues:
            print(f"  - {line}")
        return 1
    if skip_status:
        print(f"PASS: validate_atl6_starter_style_redeploy ({skip_status})")
    else:
        print("PASS: validate_atl6_starter_style_redeploy")
    print(f"  - starter-style-redeploy dir: {REDEPLOY_DIR}")
    print(f"  - train: 16 / eval: 4")
    print(f"  - environment: run_tool returns (no raise)")
    print(f"  - reward: 0.0~1.0 normalized")
    print(f"  - launcher_args: no batch_size, learning_rate present")
    if skip_status:
        print(f"  - result: {skip_status}")
    else:
        print("  - result: present, no secret-shaped strings, train/eval samples match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
