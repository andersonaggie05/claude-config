---
name: vault-ingest
description: Process PDF/docx documents into clean Markdown vault entries
---

# /vault-ingest

Convert documents into vault-compatible Markdown.

## Process

1. User provides document path or URL
2. Read document (Claude reads PDFs natively via Read tool)
3. Extract core ideas — not a full transcription, focus on:
   - Key decisions and their rationale
   - Requirements or constraints
   - Action items or deadlines
   - Technical specifications
4. Write clean Markdown to vault-docs/processed/ with frontmatter:
   ```markdown
   ---
   name: {document title}
   description: {one-line summary}
   type: processed-document
   source: {original filename}
   date-processed: {YYYY-MM-DD}
   ---
   ```
5. Add [[backlinks]] to related modules, skills, decisions
6. Archive original to vault-docs/raw/ (if local file)
7. Principle: Agent always works with processed Markdown, never raw documents
