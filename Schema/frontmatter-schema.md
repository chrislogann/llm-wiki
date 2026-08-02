
# Frontmatter Schema

## Raw source notes

Required fields:

- `Title`
- `Reference`
- `Created`
- `Processed`
- `tags`

Expected fields:

- `Author`
- `ContentType`

Template shape:

```yaml
---
Title: ""
Author: ""
Reference: ""
ContentType:
  - "markdown"
Created: YYYY-MM-DD
Processed: false
tags:
  - "source"
---
```

## Compiled Wiki notes

Allowed tags:

- `topic`
- `concept`
- `entity`
- `project`
- `log`

Template shape:

```yaml
---
tags:
  - "concept"
topics: []
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
source_count: 0
aliases: []
---
```

Rules:

- `source_count` must equal `len(sources)`.
- Each item in `sources` must point to an existing file under `Raw/Sources/`.
- The note tag must match the note location and content type.
