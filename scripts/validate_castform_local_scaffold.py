#!/usr/bin/env python3
"""
validate_castform_local_scaffold.py — 检查本地 scaffold 文件
标准库 only。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOCAL_ENV = (
    PROJECT_ROOT
    / "cases"
    / "castform-hermes-phase-closer-v0"
    / "local-validate-env"
)

REQUIRED_FILES = [
    "README.md",
    "dataset_loader.py",
    "reward.py",
    "environment_stub.py",
    "run_local_reward_smoke.py",
    "run_validate_env_stub.py",
]

FORBIDDEN_PATTERNS = [
    r"upload_training_run",
    r"launch_training_run",
    r"TrainerClient",
    r"CASTFORM_API_KEY\s*=\s*[\"']?[A-Za-z0-9_-]{8,}",
]


def main():
    errors = []

    if not LOCAL_ENV.exists():
        errors.append(f"Directory not found: {LOCAL_ENV}")
    else:
        for fname in REQUIRED_FILES:
            fpath = LOCAL_ENV / fname
            if not fpath.exists():
                errors.append(f"Missing file: {fname}")
                continue
            text = fpath.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, text):
                    errors.append(f"{fname}: contains forbidden pattern: {pattern[:40]}")

    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\nFAIL ({len(errors)} errors)")
        return 1
    else:
        print("✓ local-validate-env directory exists")
        print("✓ All required files present")
        print("✓ No forbidden patterns found")
        print("\nPASS")
        return 0


if __name__ == "__main__":
    exit(main())
