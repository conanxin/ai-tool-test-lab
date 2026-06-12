#!/usr/bin/env python3
"""
reward.py — Rule-based reward for Castform Hermes Phase Closer v0
标准库 only。
"""

import re

REQUIRED_HEADERS = [
    "阶段结论",
    "当前状态",
    "设计理由",
    "修改影响",
    "验证结果",
    "风险边界",
    "下一步",
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",
    r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9_-]{4,}",
    r"Authorization:\s*Bearer\s+\S+",
    r"PRIVATE\s+KEY",
    r"password\s*=\s*[A-Za-z0-9_-]{4,}",
    r"\d{9,}:[A-Za-z0-9_-]{10,}",
]


def score_completion(prompt: str, completion: str, ground_truth: str) -> dict:
    checks = {}
    notes = []
    score = 0.0

    # Check required headers
    for header in REQUIRED_HEADERS:
        present = header in completion
        checks[header] = present
        if present:
            score += 1.0
        else:
            notes.append(f"Missing header: {header}")

    # Check for secrets
    secret_found = False
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, completion):
            secret_found = True
            notes.append(f"Secret pattern detected: {pattern[:30]}...")

    if secret_found:
        notes.append("SECRET_DETECTED: score set to 0")
        return {
            "score": 0.0,
            "checks": checks,
            "notes": notes,
        }

    # Normalize score to 0-10
    max_score = len(REQUIRED_HEADERS)
    normalized = (score / max_score) * 10.0

    return {
        "score": round(normalized, 2),
        "checks": checks,
        "notes": notes,
    }


if __name__ == "__main__":
    # Quick smoke test
    gt = "\n".join(f"## {h}\ncontent" for h in REQUIRED_HEADERS)
    result = score_completion("prompt", gt, gt)
    print(f"Score: {result['score']}")
    print(f"Checks: {result['checks']}")
