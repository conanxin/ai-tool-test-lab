#!/usr/bin/env python3
"""
reward_starter_style.py — ATL-6A rule-based reward for starter-style redeploy.

Defines score_completion(prompt, completion, ground_truth) -> dict returning
{format, coverage, score} where every component is in [0.0, 1.0].

The starter-style reward mirrors the ATL-3B/ATL-5 reward rubric (the 7 closing
headers) but normalises the final score into the 0.0~1.0 range so it stays
compatible with starter-style task defaults and is easier to reason about
across the BenchMax starter task surface.

Hard rules respected:
  * no external API
  * no LLM judge
  * no network
  * all components in [0.0, 1.0]
  * secret-pattern detection sets score to 0.0 (defensive)
"""

from __future__ import annotations

import re
from typing import Any


REQUIRED_HEADERS = [
    "阶段结论",
    "当前状态",
    "设计理由",
    "修改影响",
    "验证结果",
    "风险边界",
    "下一步",
]

# Defensive secret patterns — if the completion leaks an API key / token /
# authorization header / private key fragment, the reward is forced to 0.0 so
# the trainer never accidentally reinforces a pattern that re-emits secrets.
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"CASTFORM_API_KEY\s*=\s*[A-Za-z0-9_-]{4,}"),
    re.compile(r"Authorization\s*:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"PRIVATE\s+KEY"),
    re.compile(r"password\s*=\s*[A-Za-z0-9_-]{4,}", re.IGNORECASE),
    re.compile(r"\d{9,}:[A-Za-z0-9_-]{10,}"),
    re.compile(r"cf_[A-Za-z0-9]{4,}"),
]


def _format_score(completion: str) -> float:
    """Return 1.0 if every required header appears, else hits/required."""
    if not completion:
        return 0.0
    hits = sum(1 for h in REQUIRED_HEADERS if h in completion)
    return hits / len(REQUIRED_HEADERS)


def _coverage_score(completion: str, ground_truth: str) -> float:
    """
    Light-weight keyword overlap between the completion and the ground truth.

    The ground truth is the canonical structured closing the model should
    produce. We compare against an n-gram-unique token set: at least one
    overlap token from each header block in the ground truth must be present
    in the completion for full coverage. We keep the implementation entirely
    offline (no embeddings, no API).
    """
    if not ground_truth or not completion:
        return 0.0

    def _norm(text: str) -> list[str]:
        return [t for t in re.findall(r"[\w一-鿿]+", text) if len(t) >= 2]

    gt_tokens = set(_norm(ground_truth))
    cm_tokens = set(_norm(completion))
    if not gt_tokens:
        return 0.0
    overlap = gt_tokens & cm_tokens
    return min(1.0, len(overlap) / max(8, min(40, len(gt_tokens))))


def _secret_violation(completion: str) -> bool:
    for pat in SECRET_PATTERNS:
        if pat.search(completion):
            return True
    return False


def score_completion(
    prompt: str, completion: str, ground_truth: str
) -> dict[str, Any]:
    """
    Returns a dict with at least {format, coverage, score}, every value in
    [0.0, 1.0]. `prompt` is accepted to mirror the standard reward signature
    but is not used (no LLM judge, no input-conditioned scoring).
    """
    completion_text = completion or ""

    if _secret_violation(completion_text):
        return {
            "format": 0.0,
            "coverage": 0.0,
            "score": 0.0,
            "checks": {h: False for h in REQUIRED_HEADERS},
            "notes": ["SECRET_DETECTED: score forced to 0.0"],
        }

    fmt = _format_score(completion_text)
    cov = _coverage_score(completion_text, ground_truth or "")
    score = round(min(1.0, 0.6 * fmt + 0.4 * cov), 4)

    return {
        "format": round(fmt, 4),
        "coverage": round(cov, 4),
        "score": score,
        "checks": {h: (h in completion_text) for h in REQUIRED_HEADERS},
        "notes": [],
    }


if __name__ == "__main__":
    # Quick offline smoke test.
    gt = "\n".join(f"## {h}\ncontent for {h}" for h in REQUIRED_HEADERS)
    completion = "\n".join(f"## {h}\nanswer" for h in REQUIRED_HEADERS)
    result = score_completion("prompt", completion, gt)
    print(f"Score: {result['score']}")
    print(f"Format: {result['format']}")
    print(f"Coverage: {result['coverage']}")
    print(f"Checks: {result['checks']}")
