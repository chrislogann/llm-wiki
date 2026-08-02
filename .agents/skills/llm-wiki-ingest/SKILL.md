
---
name: llm-wiki-ingest
description: "Use when turning Raw/Sources notes into linked Wiki notes."
version: 1.0.0
---

# LLM Wiki Ingest

1. Search `Wiki/catalog.jsonl` first.
2. Open only the compiled notes that look relevant.
3. Read the Raw source next.
4. Create or update concise Wiki notes under `Wiki/`.
5. Add the Raw source path to `sources` and keep `source_count` accurate.
6. Rebuild the catalog and run lint checks before finishing.
