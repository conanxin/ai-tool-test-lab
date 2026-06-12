#!/usr/bin/env python3
"""
check_secrets.py — 扫描敏感信息泄露

标准库 only。
允许占位符：<CASTFORM_API_KEY>, <TOKEN_REDACTED>, <API_KEY_REDACTED> 等。
输出 PASS / FAIL。
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# 占位符白名单：包含这些的整行不算敏感信息
ALLOWED_PLACEHOLDERS = [
    "<CASTFORM_API_KEY>",
    "<TOKEN_REDACTED>",
    "<API_KEY_REDACTED>",
    "<API_KEY>",
    "<TOKEN>",
]

# 敏感模式：(正则, 描述)
PATTERNS = [
    (r"CASTFORM_API_KEY\s*=\s*['\"]?[a-zA-Z0-9_\-]{10,}", "CASTFORM_API_KEY with real value"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI-style secret key"),
    (r"api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{8,}", "api_key assignment"),
    (r"token\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}", "token assignment"),
    (r"bot\s+token\s*[:=]\s*['\"][a-zA-Z0-9_\-]{10,}", "bot token"),
    (r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----", "private key"),
    (r"password\s*[:=]\s*['\"][^'\"]{3,}", "password assignment"),
]

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", ".venv-castform-local", ".venv*", "node_modules"}
IGNORE_FILES = {"check_secrets.py"}

TEXT_EXTENSIONS = {
    ".py", ".md", ".html", ".css", ".js", ".json", ".jsonl", ".txt", ".yml", ".yaml", ".sh"
}


def is_placeholder_line(line):
    for ph in ALLOWED_PLACEHOLDERS:
        if ph in line:
            return True
    return False


def scan_file(path):
    findings = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return findings

    for lineno, line in enumerate(lines, 1):
        if is_placeholder_line(line):
            continue
        for pattern, desc in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                snippet = line.strip()
                findings.append((str(path.relative_to(PROJECT_ROOT)), lineno, desc, snippet))
                break  # one finding per line is enough
    return findings


def main():
    print("=== check_secrets.py ===")
    all_findings = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in files:
            if fname in IGNORE_FILES:
                continue
            if Path(fname).suffix.lower() not in TEXT_EXTENSIONS:
                continue
            path = Path(root) / fname
            all_findings.extend(scan_file(path))

    if not all_findings:
        print("PASS")
        return 0

    print(f"FAIL: found {len(all_findings)} potential secret(s)")
    for rel, lineno, desc, snippet in all_findings:
        print(f"  {rel}:{lineno} — {desc}")
        print(f"    {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
