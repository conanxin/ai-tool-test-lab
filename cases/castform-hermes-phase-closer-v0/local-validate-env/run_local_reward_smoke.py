#!/usr/bin/env python3
"""
run_local_reward_smoke.py — 本地 reward smoke 测试
标准库 only。
"""

import json
from pathlib import Path
from reward import score_completion


def main():
    base = Path(__file__).parent.parent
    eval_path = base / "sample-eval.jsonl"

    samples = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))

    # Test 1: ground_truth as completion should score high
    passed = 0
    for i, sample in enumerate(samples[:3], 1):
        result = score_completion(sample["prompt"], sample["ground_truth"], sample["ground_truth"])
        print(f"Test {i} (good completion): score={result['score']}")
        if result["score"] >= 7.0:
            passed += 1
        else:
            print(f"  FAIL: expected >= 7.0, got {result['score']}")
            print(f"  Notes: {result['notes']}")

    # Test 2: bad completion should score low
    bad_completion = "This is a bad completion with no headers."
    result = score_completion("prompt", bad_completion, "")
    print(f"Test 4 (bad completion): score={result['score']}")
    if result["score"] < 3.0:
        passed += 1
    else:
        print(f"  FAIL: expected < 3.0, got {result['score']}")

    # Test 3: completion with secret should score 0
    secret_completion = "## 阶段结论\nok\n## 当前状态\nPASS\n## 设计理由\nok\n## 修改影响\nok\n## 验证结果\nok\n## 风险边界\nok\n## 下一步\nok\nCASTFORM_API_KEY=sk-1234567890abcdef"
    result = score_completion("prompt", secret_completion, "")
    print(f"Test 5 (secret completion): score={result['score']}")
    if result["score"] == 0.0:
        passed += 1
    else:
        print(f"  FAIL: expected 0.0, got {result['score']}")

    total = 5
    print(f"\nPassed: {passed}/{total}")
    if passed == total:
        print("PASS")
    else:
        print("FAIL")


if __name__ == "__main__":
    main()
