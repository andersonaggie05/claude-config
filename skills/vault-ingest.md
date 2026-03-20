---
name: vault-ingest
description: Process PDF/docx documents into clean Markdown notes in ~/vault/inbox/
---

# /vault-ingest

Convert documents into vault-compatible Markdown notes.

## Process

1. User provides document path or URL
2. Read document (Claude reads PDFs natively via Read tool)
3. Extract core ideas — not a full transcription, focus on:
   - Key decisions and their rationale
   - Requirements or constraints
   - Action items or deadlines
   - Technical specifications
4. Write clean Markdown to ~/vault/inbox/ with frontmatter:
   ```markdown
   ---
   created: {YYYY-MM-DD}
   source: {original filename or URL}
   status: inbox
   tags: [{relevant tags}]
   ---
   ```
5. Add [[wikilinks]] to related vault notes (claims, frameworks, sources, projects, etc.)
6. Run `qmd embed` via Bash to update the search index
7. Principle: Agent always works with processed Markdown, never raw documents
