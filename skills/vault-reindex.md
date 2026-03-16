---
name: vault-reindex
description: Rebuild MEMORY.md index, verify all backlinks, update tags, regenerate canvases
---

# /vault-reindex

Full vault reindex and consistency check.

## Process

1. Scan all .md files in modules/, memory/, skills/
2. Rebuild MEMORY.md index from actual files present
3. Verify every [[wikilink]] resolves to an existing file
4. Collect all #tags used across files, report inventory
5. Regenerate system-architecture.canvas from current file state
6. Report: files indexed, links verified, tags found, canvases regenerated
