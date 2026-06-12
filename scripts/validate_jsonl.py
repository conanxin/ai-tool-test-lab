#!/usr/bin/env python3
"""
validate_jsonl.py — 验证 JSONL 样本格式

标准库 only。
检查：
- 每行必须是合法 JSON
- 每行必须包含 prompt 和 ground_truth
- prompt / ground_truth 必须是非空字符串
- ground_truth 必须包含以下标题：
  阶段结论、当前状态、设计理由、修改影响、验证结果、风险边界、下一步

输出 PASS / FAIL
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CASE_DIR = PROJECT_ROOT / "cases" / "castform-hermes-phase-closer-v0"

REQUIRED_HEADERS = [
    "阶段结论",
    "当前状态",
    "设计理由",
    "修改影响",
    "验证结果",
    "风险边界",
    "下一步",
]


def validate_jsonl_file(path: Path) -> list:
    errors = []
    if not path.exists():
        errors.append(f"File not found: {path}")
        return errors

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: invalid JSON — {e}")
                continue

            if not isinstance(obj, dict):
                errors.append(f"Line {i}: not a JSON object")
                continue

            for key in ("prompt", "ground_truth"):
                if key not in obj:
                    errors.append(f"Line {i}: missing '{key}'")
                    continue
                val = obj[key]
                if not isinstance(val, str) or not val.strip():
                    errors.append(f"Line {i}: '{key}' is empty or not a string")

            gt = obj.get("ground_truth", "")
            if isinstance(gt, str):
                missing = [h for h in REQUIRED_HEADERS if h not in gt]
                if missing:
                    errors.append(f"Line {i}: ground_truth missing headers: {', '.join(missing)}")

    return errors


def main():
    all_errors = []
    files = [
        CASE_DIR / "sample-train.jsonl",
        CASE_DIR / "sample-eval.jsonl",
    ]

    for path in files:
        print(f"Checking: {path.name}")
        errs = validate_jsonl_file(path)
        if errs:
            for e in errs:
                print(f"  ✗ {e}")
            all_errors.extend(errs)
        else:
            # Count lines
            count = 0
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            print(f"  ✓ {count} valid samples")

    if all_errors:
        print(f"\nFAIL ({len(all_errors)} errors)")
        sys.exit(1)
    else:
        print("\nPASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
