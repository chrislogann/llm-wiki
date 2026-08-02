
---
name: llm-wiki-lint
description: "Use when validating Wiki notes, source coverage, and generated indexes."
version: 1.0.0
---

# LLM Wiki Lint

Run the deterministic maintenance gate:

```bash
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```

Fix any missing tags, broken source links, stale counts, or coverage mismatches before committing.
