
---
name: llm-wiki-maintain
description: "Use when updating indexes, manifests, and maintenance checks for the LLM Wiki."
version: 1.0.0
---

# LLM Wiki Maintain

1. Update notes under `Wiki/` or `Raw/Sources/`.
2. Rebuild `Wiki/catalog.jsonl` and `Wiki/index.md`.
3. Refresh `Schema/source-manifest.jsonl` when source coverage changes.
4. Run lint and audit checks.
5. Commit only after the gate passes.
