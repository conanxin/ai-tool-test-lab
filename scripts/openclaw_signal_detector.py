#!/usr/bin/env python3
"""
openclaw_signal_detector.py

Detect OpenClaw-specific signals from session text or JSONL input.
Used by ATL-EVOMAP-3B to test whether the Phase 3A Gene
(gene_distilled_openclaw-tool-use-discipline) can be matched by a
local selector that ingests detector output.

Usage:
    python3 scripts/openclaw_signal_detector.py \
        --input <path-to-session-text-or-jsonl> \
        --output <path-to-output-json>

Exit codes:
    0 = success (signals emitted or empty), 1 = error

Hard constraints:
- No .env reads
- No recursive repo scan
- Only reads the explicit --input path
- Stdlib only
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "0.1.0"
DETECTOR_NAME = "openclaw_signal_detector"

# Tool call patterns
TOOL_PATTERNS = {
    "exec":   re.compile(r"\[TOOL:\s*exec\b", re.IGNORECASE),
    "read":   re.compile(r"\[TOOL:\s*read\b", re.IGNORECASE),
    "search": re.compile(r"\[TOOL:\s*search\b", re.IGNORECASE),
    "edit":   re.compile(r"\[TOOL:\s*edit\b", re.IGNORECASE),
    "write":  re.compile(r"\[TOOL:\s*write\b", re.IGNORECASE),
}

# Grep-like file read patterns (when not via [TOOL: read])
GREP_LIKE_PATTERNS = [
    re.compile(r"\bgrep\b"),
    re.compile(r"\brg\b"),
    re.compile(r"\bcat\b"),
    re.compile(r"\bhead\b"),
    re.compile(r"\btail\b"),
    re.compile(r"\bsed\s+-i\b"),
    re.compile(r"\bawk\s+-i\b\s+inplace\b"),
]

# In-place mutation patterns
INPLACE_MUTATION_PATTERNS = [
    re.compile(r"\bsed\s+-i\b"),
    re.compile(r"\bawk\s+-i\b\s+inplace\b"),
    re.compile(r"\bpython\s+-c\s+['\"]?[^'\"]*rewrite"),
    re.compile(r"\bperl\s+-i\s+-pe\b"),
]

# Repo context patterns
REPO_CONTEXT_AI_TOOL = re.compile(r"ai-tool-test-lab", re.IGNORECASE)
REPO_CONTEXT_ATL_REPO = re.compile(r"/mnt/d/AI/ai-tool-test-lab|/AI/ai-tool-test-lab", re.IGNORECASE)

# OpenClaw context patterns
OPENCLAW_CONTEXT_PATTERNS = [
    re.compile(r"\bOpenClaw\b", re.IGNORECASE),
    re.compile(r"\bopenclaw\b"),
    re.compile(r"\bAgent\b"),
    re.compile(r"session\s+tail", re.IGNORECASE),
    re.compile(r"recent\s+session", re.IGNORECASE),
    re.compile(r"\bcwd\s*[:=]"),
    re.compile(r"workspace", re.IGNORECASE),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect OpenClaw-specific signals from session text or JSONL.",
    )
    p.add_argument("--input", required=True, help="Path to input session file (text or jsonl)")
    p.add_argument("--output", required=True, help="Path to output JSON file")
    return p.parse_args()


def detect_signals(content: str) -> dict:
    """Run detection rules and return a structured result."""
    # 1. Tool call counts
    counts = {
        "exec_count":   len(TOOL_PATTERNS["exec"].findall(content)),
        "read_count":   len(TOOL_PATTERNS["read"].findall(content)),
        "search_count": len(TOOL_PATTERNS["search"].findall(content)),
        "edit_count":   len(TOOL_PATTERNS["edit"].findall(content)),
        "write_count":  len(TOOL_PATTERNS["write"].findall(content)),
    }

    grep_hits = 0
    for pat in GREP_LIKE_PATTERNS:
        grep_hits += len(pat.findall(content))

    inplace_hits = 0
    for pat in INPLACE_MUTATION_PATTERNS:
        inplace_hits += len(pat.findall(content))

    repo_hits_ai_tool = len(REPO_CONTEXT_AI_TOOL.findall(content))
    repo_hits_atl = len(REPO_CONTEXT_ATL_REPO.findall(content))

    openclaw_hits = 0
    openclaw_evidence = []
    for pat in OPENCLAW_CONTEXT_PATTERNS:
        matches = pat.findall(content)
        if matches:
            openclaw_hits += len(matches)
            openclaw_evidence.append(pat.pattern)

    # 2. Compute exec ratio
    base = max(1, counts["read_count"] + counts["search_count"] + counts["edit_count"] + counts["write_count"])
    exec_ratio = counts["exec_count"] / base

    # 3. Build signals list
    signals = []

    # Rule 6: exec ratio > 0.5 -> repeated_tool_usage:exec
    if counts["exec_count"] > 0 and exec_ratio > 0.5:
        signals.append({
            "key": "repeated_tool_usage:exec",
            "score": min(1.0, exec_ratio),
            "evidence": [
                f"exec_count={counts['exec_count']}",
                f"exec_ratio={exec_ratio:.2f} > 0.5",
            ],
            "reason": f"exec call count ({counts['exec_count']}) is more than half of all structured file tool calls ({base})",
        })

    # Rule 7: exec on grep/cat/head/tail/sed -i/awk -i inplace -> tool_bypass:exec-on-grep
    if counts["exec_count"] > 0 and grep_hits > 0:
        signals.append({
            "key": "tool_bypass:exec-on-grep",
            "score": min(1.0, grep_hits / max(1, counts["exec_count"])),
            "evidence": [
                f"exec_count={counts['exec_count']}",
                f"grep_like_pattern_hits={grep_hits}",
            ],
            "reason": "exec invocations paired with grep/cat/head/tail/sed -i/awk -i inplace bypass the read/search tool",
        })

    # Rule 8: sed -i / awk -i inplace / python rewrite -> protocol_drift:wrong-tool-for-file-read
    if inplace_hits > 0:
        signals.append({
            "key": "protocol_drift:wrong-tool-for-file-read",
            "score": min(1.0, inplace_hits / 3.0),
            "evidence": [
                f"inplace_mutation_hits={inplace_hits}",
            ],
            "reason": "in-place shell mutation patterns (sed -i, awk -i inplace, python rewrite) bypass the edit tool",
        })

    # Rule 9: cwd/repo contains ai-tool-test-lab -> repo_context:ai-tool-test-lab
    if repo_hits_ai_tool > 0 or repo_hits_atl > 0:
        signals.append({
            "key": "repo_context:ai-tool-test-lab",
            "score": 1.0 if repo_hits_atl > 0 else 0.6,
            "evidence": [
                f"ai-tool-test-lab_str_hits={repo_hits_ai_tool}",
                f"atl_path_hits={repo_hits_atl}",
            ],
            "reason": "session cwd or repo name matches ai-tool-test-lab",
        })

    # Rule 10: OpenClaw / openclaw / Agent / session tail -> session_context:openclaw
    if openclaw_hits > 0:
        signals.append({
            "key": "session_context:openclaw",
            "score": min(1.0, openclaw_hits / 3.0),
            "evidence": openclaw_evidence[:5] + [f"openclaw_hits={openclaw_hits}"],
            "reason": "session text contains OpenClaw markers (OpenClaw/openclaw/Agent/session tail/cwd/workspace)",
        })

    return {
        "detector": DETECTOR_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": None,  # filled by caller
            "size_bytes": len(content),
            "lines": content.count("\n") + 1,
        },
        "signals": signals,
        "summary": {
            "exec_count": counts["exec_count"],
            "read_count": counts["read_count"],
            "search_count": counts["search_count"],
            "edit_count": counts["edit_count"],
            "write_count": counts["write_count"],
            "exec_ratio": round(exec_ratio, 3),
            "grep_like_hits": grep_hits,
            "inplace_mutation_hits": inplace_hits,
            "openclaw_marker_hits": openclaw_hits,
        },
    }


def read_input(path: Path) -> str:
    """Read input file. Supports plain text or JSONL.
    For JSONL, join all line contents (stripped of JSON envelope)
    to maximize pattern match coverage."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    # Flatten common fields into text
                    parts = []
                    for k in ("type", "kind", "id", "ts", "content", "text", "message", "tool", "tool_name"):
                        if k in obj:
                            parts.append(str(obj[k]))
                    if "args" in obj and isinstance(obj["args"], dict):
                        for v in obj["args"].values():
                            parts.append(str(v))
                    if "signal" in obj and isinstance(obj["signal"], dict):
                        for v in obj["signal"].values():
                            parts.append(str(v))
                    lines.append(" ".join(parts))
                except json.JSONDecodeError:
                    # Not JSON, treat as plain text line
                    lines.append(line)
        return "\n".join(lines)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        content = read_input(input_path)
    except Exception as e:
        print(f"ERROR: failed to read input: {e}", file=sys.stderr)
        return 1

    result = detect_signals(content)
    result["input"]["path"] = str(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print summary to stdout
    n = len(result["signals"])
    print(f"Detected {n} signal(s) from {input_path} -> {output_path}")
    for s in result["signals"]:
        print(f"  - {s['key']} (score={s['score']:.2f})")
    print(f"  summary: {result['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
