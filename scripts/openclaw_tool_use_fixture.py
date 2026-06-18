#!/usr/bin/env python3
"""
openclaw_tool_use_fixture.py

A minimal, stdlib-only helper used by ATL-EVOMAP-3C-V2 to trigger a *real*
(non-hollow) code diff in the ai-tool-test-lab repository. It accepts a
session-log-style text file and emits a JSON summary that downstream
Evolver-style tooling can use to detect OpenClaw tool-use patterns.

Hard requirements satisfied by this script:
  - Python stdlib only (no third-party imports).
  - No .env reads.
  - No recursive repo scans.
  - Only reads a single --input file.
  - Does not modify the working tree.
  - Does not print secrets / tokens.

Usage:
    python3 scripts/openclaw_tool_use_fixture.py \
        --input cases/evomap-evolver-openclaw-v0/phase3c-v2-non-hollow-solidify/fixtures/session-tool-use-sample.txt
"""

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_LINE_RE = re.compile(r"\[TOOL:\s*(exec|read|edit|search)\]")
SESSION_CTX_RE = re.compile(r"OpenClaw\s+session\s+context", re.IGNORECASE)
REPO_CTX_RE = re.compile(r"cwd\s*=\s*(\S+)")
TOOL_BYPASS_HINT_RE = re.compile(
    r"exec\s+on\s+grep|exec-on-grep|using\s+exec\s+instead\s+of\s+search",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenClaw session tool-use fixture summarizer.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a session tool-use log text file.",
    )
    return parser.parse_args()


def count_tool_uses(text: str) -> dict:
    counts = {"exec": 0, "read": 0, "edit": 0, "search": 0}
    for m in TOOL_LINE_RE.finditer(text):
        kind = m.group(1).lower()
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def main() -> int:
    args = parse_args()
    input_path: Path = args.input
    if not input_path.is_file():
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"input file not found: {input_path}",
                },
                ensure_ascii=False,
            ),
            file=sys.stdout,
        )
        return 2

    text = input_path.read_text(encoding="utf-8", errors="replace")
    counts = count_tool_uses(text)
    total_tool_uses = sum(counts.values())
    exec_count = counts["exec"]
    read_count = counts["read"]
    edit_count = counts["edit"]
    search_count = counts["search"]
    exec_ratio = (
        round(exec_count / total_tool_uses, 4) if total_tool_uses else 0.0
    )

    has_session_context = bool(SESSION_CTX_RE.search(text))
    cwd_match = REPO_CTX_RE.search(text)
    repo_context = cwd_match.group(1) if cwd_match else None
    has_repo_context = repo_context is not None
    has_tool_bypass_hint = bool(TOOL_BYPASS_HINT_RE.search(text))

    summary = {
        "ok": True,
        "input": str(input_path),
        "exec_count": exec_count,
        "read_count": read_count,
        "edit_count": edit_count,
        "search_count": search_count,
        "total_tool_uses": total_tool_uses,
        "exec_ratio": exec_ratio,
        "has_session_context": has_session_context,
        "has_repo_context": has_repo_context,
        "repo_context": repo_context,
        "has_tool_bypass_hint": has_tool_bypass_hint,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
