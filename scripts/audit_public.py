#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", ".obsidian", ".cache", ".venv", "__pycache__", "node_modules"}
IGNORE_FILES = {"source-manifest.jsonl", "catalog.jsonl"}
SECRET_PATTERNS = [
    re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)secret\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)token\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}"),
]
LOCAL_PATH_PATTERNS = [
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
]


def should_skip(path: Path) -> bool:
    return bool(set(path.parts) & IGNORE_DIRS)


def main() -> int:
    problems: list[str] = []
    for path in REPO.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue
        if path.name in IGNORE_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = path.relative_to(REPO).as_posix()
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                problems.append(f"{rel}: looks like a secret or private key")
                break
        for pat in LOCAL_PATH_PATTERNS:
            if pat.search(text):
                problems.append(f"{rel}: contains machine-local path")
                break
    if problems:
        print("Public audit failed:")
        for item in problems:
            print(f"- {item}")
        return 1
    print("Public audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
