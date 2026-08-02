
# Workflow Examples

## Ingest

1. Search `Wiki/catalog.jsonl` for related compiled notes.
2. Open the most relevant compiled notes.
3. Add or update a focused note in `Wiki/`.
4. Link the note back to the Raw source in `sources`.
5. Run the maintenance checks.

## Query

```bash
python3 scripts/wiki_tool.py search-catalog --query "llm wiki"
```

## Maintenance

```bash
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```
