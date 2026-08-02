
# AGENTS.md

This repository is an Obsidian-based LLM Wiki.

## Ground rules

- Treat `Raw/Sources/` as source material, not as compiled knowledge.
- Write reusable knowledge only under `Wiki/`.
- Keep every compiled Wiki note linked to one or more Raw sources.
- Search `Wiki/catalog.jsonl` before opening broad Raw context.
- Run `build`, `lint`, and source checks before commits.
- Do not invent citations or create unsupported claims.

## Operational order

1. Search the catalog first.
2. Open only the most relevant compiled notes.
3. Read Raw sources only when the compiled notes are insufficient.
4. After editing, run:
   - `python3 scripts/wiki_tool.py build`
   - `python3 scripts/wiki_tool.py lint`
   - `python3 scripts/wiki_tool.py source-lint`
   - `python3 scripts/audit_public.py`
5. Commit only after the checks pass.
