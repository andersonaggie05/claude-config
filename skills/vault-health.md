---
name: vault-health
description: Run full vault hygiene check — orphans, broken links, staleness, token budgets, connection density
---

# /vault-health

Run a comprehensive health check on the ~/.claude/ vault and ~/vault/.

## Checks

1. **Orphan detection**: Find .md files in modules/, memory/, skills/ that no other file links to via [[wikilink]]
2. **Broken links**: Find [[wikilinks]] that point to files that don't exist (scan modules/, memory/, skills/, and ~/vault/)
3. **Staleness**: Find memory files not modified in 30+ days — flag for review
4. **Token budgets**: Count words in each category, compare against limits:
   - Workflow-protocol skill: 5,000 words max
   - Domain skills (per project): 10,000 words max
   - Knowledge modules (all): 3,000 words max
   - Memory files (all): 5,000 words max
   - CLAUDE.md: 800 words max
5. **Connection density**: For each module, check it has >=2 connections in its ## Connections section
6. **Vault inbox staleness**: Find notes in ~/vault/inbox/ older than 7 days — flag for triage
7. **Vault orphan detection**: Find .md files in ~/vault/ that no other vault note links to via [[wikilink]]
8. **qmd index freshness**: Run `qmd status` to check if embeddings are up to date
9. **Vault size/growth**: Count total notes in ~/vault/ and notes added in last 7/30 days

## Output Format

```
VAULT HEALTH REPORT — {date}
================================
Orphans: {count} files ({list})
Broken links: {count} ({list})
Stale files: {count} (>30 days: {list})
Token budgets: {category}: {current}/{max} ({percentage}%)
Connection gaps: {count} modules with <2 connections
--- Obsidian Vault ---
Inbox stale: {count} notes >7 days old ({list})
Vault orphans: {count} unlinked notes ({list})
qmd index: {status from qmd status}
Vault size: {total} notes ({added_7d} added last 7d, {added_30d} last 30d)
================================
Overall: HEALTHY | NEEDS ATTENTION | OVERHAUL RECOMMENDED
```
