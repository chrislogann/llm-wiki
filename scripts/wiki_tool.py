#!/usr/bin/env python3
"""Deterministic maintenance tooling for the LLM Wiki starter."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RAW_SOURCES = REPO / "Raw" / "Sources"
WIKI = REPO / "Wiki"
SCHEMA = REPO / "Schema"
ALLOWED_TAGS = {"topic", "concept", "entity", "project", "log"}
NOTE_FOLDERS = ["Topics", "Concepts", "Entities", "Projects", "Logs"]
INDEX_EXCLUDES = {"index.md", "catalog.jsonl"}
SOURCE_REQUIRED = ["Title", "Reference", "Created", "Processed", "tags"]


@dataclass
class Note:
    path: Path
    frontmatter: dict[str, Any]
    body: str


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    if text in {"[]", "[ ]"}:
        return []
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            pass
    return text


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :])
    data: dict[str, Any] = {}
    current_key = None
    mode = None
    for raw in fm_lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if mode == "list" and current_key and (line.startswith("  - ") or line.startswith("- ")):
            item = line[4:] if line.startswith("  - ") else line[2:]
            data[current_key].append(parse_scalar(item))
            continue
        m = re.match(r"^([A-Za-z0-9_]+):(?:\s*(.*))?$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2) or ""
        current_key = key
        if value == "":
            data[key] = []
            mode = "list"
            continue
        if value == "[]":
            data[key] = []
            mode = None
            continue
        parsed = parse_scalar(value)
        data[key] = parsed
        mode = "list" if isinstance(parsed, list) else None
    return data, body


def read_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    return Note(path=path, frontmatter=fm, body=body)


def ensure_dirs() -> None:
    for p in [WIKI, SCHEMA, RAW_SOURCES]:
        p.mkdir(parents=True, exist_ok=True)
    for folder in NOTE_FOLDERS:
        (WIKI / folder).mkdir(parents=True, exist_ok=True)


def discover_raw_sources() -> list[Path]:
    if not RAW_SOURCES.exists():
        return []
    return sorted(p for p in RAW_SOURCES.rglob("*.md") if p.is_file())


def discover_compiled_notes() -> list[Path]:
    if not WIKI.exists():
        return []
    notes = []
    for path in WIKI.rglob("*.md"):
        if path.name in INDEX_EXCLUDES:
            continue
        notes.append(path)
    return sorted(p for p in notes if p.is_file())


def source_title(note: Note, fallback: str) -> str:
    title = note.frontmatter.get("Title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return fallback


def compiled_title(note: Note, fallback: str) -> str:
    for line in note.body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    title = note.frontmatter.get("title") or note.frontmatter.get("Title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return fallback


def compiled_sources(note: Note) -> list[str]:
    sources = note.frontmatter.get("sources", [])
    if not isinstance(sources, list):
        return []
    return [s for s in sources if isinstance(s, str)]


def note_tag(note: Note, path: Path) -> str | None:
    tags = note.frontmatter.get("tags", [])
    if not isinstance(tags, list):
        return None
    allowed = [t for t in tags if isinstance(t, str) and t in ALLOWED_TAGS]
    if len(allowed) != 1:
        return None
    tag = allowed[0]
    expected = {
        "Topics": "topic",
        "Concepts": "concept",
        "Entities": "entity",
        "Projects": "project",
        "Logs": "log",
    }.get(path.parent.name)
    if expected and tag != expected:
        return None
    if path.name == "log.md" and tag != "log":
        return None
    return tag


def manifest_path() -> Path:
    return SCHEMA / "source-manifest.jsonl"


def load_manifest() -> dict[str, dict[str, Any]]:
    path = manifest_path()
    if not path.exists():
        return {}
    data: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        data[obj["path"]] = obj
    return data


def coverage_map() -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = defaultdict(list)
    for path in discover_compiled_notes():
        note = read_note(path)
        if not note_tag(note, path):
            continue
        for src in compiled_sources(note):
            coverage[src].append(rel(path))
    return {k: sorted(set(v)) for k, v in coverage.items()}


def build_catalog_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in discover_compiled_notes():
        note = read_note(path)
        tag = note_tag(note, path)
        if not tag:
            continue
        entries.append({
            "path": rel(path),
            "title": compiled_title(note, path.stem),
            "tag": tag,
            "topics": note.frontmatter.get("topics", []) if isinstance(note.frontmatter.get("topics", []), list) else [],
            "sources": compiled_sources(note),
            "updated": str(note.frontmatter.get("updated", "")),
        })
    return sorted(entries, key=lambda item: item["path"])


def doctor() -> int:
    ensure_dirs()
    rows = [
        ("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
        ("Raw sources", str(len(discover_raw_sources()))),
        ("Compiled notes", str(len(discover_compiled_notes()))),
        ("Catalog", "present" if (WIKI / "catalog.jsonl").exists() else "missing"),
        ("Source manifest", "present" if manifest_path().exists() else "missing"),
        ("Wiki folder", "present" if WIKI.exists() else "missing"),
        ("Schema folder", "present" if SCHEMA.exists() else "missing"),
    ]
    width = max(len(k) for k, _ in rows)
    print("Doctor check")
    for key, value in rows:
        print(f"- {key.ljust(width)} : {value}")
    return 0


def build() -> int:
    ensure_dirs()
    entries = build_catalog_entries()
    catalog = WIKI / "catalog.jsonl"
    catalog.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + ("\n" if entries else ""), encoding="utf-8")

    by_folder: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        folder = Path(entry["path"]).parent.name
        by_folder[folder].append(entry)

    root_lines = ["# Wiki Index", "", f"Compiled notes: {len(entries)}", "", "## Folders"]
    for folder in NOTE_FOLDERS:
        root_lines.append(f"- [{folder}]({folder}/index.md) — {len(by_folder.get(folder, []))}")
    if (WIKI / "log.md").exists():
        root_lines.append("- [Root log](log.md)")
    root_lines.extend(["", "## Catalog", "", "- [catalog.jsonl](catalog.jsonl)"])
    (WIKI / "index.md").write_text("\n".join(root_lines) + "\n", encoding="utf-8")

    for folder in NOTE_FOLDERS:
        folder_path = WIKI / folder
        folder_entries = sorted(by_folder.get(folder, []), key=lambda item: (item["title"].lower(), item["path"]))
        lines = [f"# {folder} Index", "", f"Notes: {len(folder_entries)}"]
        if folder_entries:
            lines.extend(["", "| Title | File | Updated |", "| --- | --- | --- |"])
            for entry in folder_entries:
                filename = Path(entry["path"]).name
                lines.append(f"| {entry['title']} | [{filename}]({filename}) | {entry['updated']} |")
        else:
            lines.extend(["", "No notes yet."])
        (folder_path / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {rel(catalog)} and index files")
    return 0


def lint() -> int:
    errors: list[str] = []
    for path in discover_compiled_notes():
        note = read_note(path)
        tag = note_tag(note, path)
        if not tag:
            errors.append(f"{rel(path)}: invalid or missing compiled tag")
            continue
        sources = compiled_sources(note)
        if note.frontmatter.get("source_count") != len(sources):
            errors.append(f"{rel(path)}: source_count does not match sources")
        for src in sources:
            if not src.startswith("Raw/Sources/"):
                errors.append(f"{rel(path)}: source outside Raw/Sources -> {src}")
            elif not (REPO / src).exists():
                errors.append(f"{rel(path)}: missing source file -> {src}")

    for path in discover_raw_sources():
        note = read_note(path)
        missing = [field for field in SOURCE_REQUIRED if field not in note.frontmatter]
        if missing:
            errors.append(f"{rel(path)}: missing source fields {', '.join(missing)}")
        tags = note.frontmatter.get("tags")
        if not isinstance(tags, list) or "source" not in tags:
            errors.append(f"{rel(path)}: source tags must include 'source'")

    if errors:
        eprint("Lint failed:")
        for err in errors:
            eprint(f"- {err}")
        return 1
    print("Lint passed")
    return 0


def source_scan(update: bool = False, accept_covered: bool = False) -> int:
    ensure_dirs()
    raw_sources = discover_raw_sources()
    coverage = coverage_map()
    manifest_rows: list[dict[str, Any]] = []
    for path in raw_sources:
        note = read_note(path)
        relpath = rel(path)
        covered_by = coverage.get(relpath, [])
        processed = bool(note.frontmatter.get("Processed")) or (accept_covered and bool(covered_by))
        manifest_rows.append({
            "path": relpath,
            "title": source_title(note, path.stem),
            "processed": processed,
            "covered_by": covered_by,
            "updated": date.today().isoformat(),
        })
    manifest_rows.sort(key=lambda item: item["path"])
    if update:
        path = manifest_path()
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in manifest_rows) + ("\n" if manifest_rows else ""), encoding="utf-8")
        print(f"Updated {rel(path)}")
    else:
        for row in manifest_rows:
            print(json.dumps(row, ensure_ascii=False))
    return 0


def source_lint() -> int:
    errors: list[str] = []
    manifest = load_manifest()
    coverage = coverage_map()
    for path in discover_raw_sources():
        note = read_note(path)
        relpath = rel(path)
        missing = [field for field in SOURCE_REQUIRED if field not in note.frontmatter]
        if missing:
            errors.append(f"{relpath}: missing source fields {', '.join(missing)}")
        covered = coverage.get(relpath, [])
        if bool(note.frontmatter.get("Processed")) and not covered:
            errors.append(f"{relpath}: marked Processed but has no Wiki coverage")
        man = manifest.get(relpath)
        if man and man.get("covered_by") != covered:
            errors.append(f"{relpath}: manifest coverage is stale")
        if man and man.get("processed") and not covered:
            errors.append(f"{relpath}: manifest marks processed but no Wiki coverage")
    if errors:
        eprint("Source lint failed:")
        for err in errors:
            eprint(f"- {err}")
        return 1
    print("Source lint passed")
    return 0


def source_delta() -> int:
    manifest = load_manifest()
    raw = {rel(path) for path in discover_raw_sources()}
    delta = sorted(raw - set(manifest))
    if delta:
        print("Unrepresented Raw sources:")
        for item in delta:
            print(f"- {item}")
    else:
        print("No Raw source delta")
    return 0


def source_coverage() -> int:
    coverage = coverage_map()
    if not coverage:
        print("No source coverage yet")
        return 0
    for src in sorted(coverage):
        print(json.dumps({"path": src, "covered_by": coverage[src]}, ensure_ascii=False))
    return 0


def search_catalog(query: str) -> int:
    path = WIKI / "catalog.jsonl"
    if not path.exists():
        print("Catalog is missing")
        return 1
    q = query.lower().strip()
    hits = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        blob = " ".join(str(obj.get(k, "")) for k in ["path", "title", "tag", "topics", "sources"]).lower()
        if q in blob:
            hits.append(obj)
    if not hits:
        print("No catalog hits")
        return 0
    for obj in hits:
        print(json.dumps(obj, ensure_ascii=False))
    return 0


def log(title: str, details: str) -> int:
    ensure_dirs()
    path = WIKI / "log.md"
    today = date.today().isoformat()
    if not path.exists():
        lines = [
            "---",
            "tags:",
            '  - "log"',
            "topics: []",
            "status: seed",
            f"created: {today}",
            f"updated: {today}",
            "sources: []",
            "source_count: 0",
            "aliases: []",
            "---",
            "",
            "# Log",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {today} — {title}\n\n{details}\n")
    print(f"Appended to {rel(path)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wiki_tool.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    sub.add_parser("build")
    sub.add_parser("lint")
    sub.add_parser("source-lint")
    sub.add_parser("source-delta")
    sub.add_parser("source-coverage")

    sscan = sub.add_parser("source-scan")
    sscan.add_argument("--update", action="store_true")
    sscan.add_argument("--accept-covered", action="store_true")

    search = sub.add_parser("search-catalog")
    search.add_argument("--query", required=True)

    logp = sub.add_parser("log")
    logp.add_argument("--title", required=True)
    logp.add_argument("--details", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        return doctor()
    if args.cmd == "build":
        return build()
    if args.cmd == "lint":
        return lint()
    if args.cmd == "source-scan":
        return source_scan(update=args.update, accept_covered=args.accept_covered)
    if args.cmd == "source-lint":
        return source_lint()
    if args.cmd == "source-delta":
        return source_delta()
    if args.cmd == "source-coverage":
        return source_coverage()
    if args.cmd == "search-catalog":
        return search_catalog(args.query)
    if args.cmd == "log":
        return log(args.title, args.details)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
