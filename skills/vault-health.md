---
name: vault-health
description: Run full vault hygiene check — orphans, broken links, staleness, token budgets, connection density
---

# /vault-health

Run a comprehensive health check on the ~/.claude/ vault.

## Checks

1. **Orphan detection**: Find .md files in modules/, memory/, skills/ that no other file links to via [[wikilink]]
2. **Broken links**: Find [[wikilinks]] that point to files that don't exist
3. **Staleness**: Find memory files not modified in 30+ days — flag for review
4. **Token budgets**: Count words in each category, compare against limits:
   - Workflow-protocol skill: 5,000 words max
   - Domain skills (per project): 10,000 words max
   - Knowledge modules (all): 3,000 words max
   - Memory files (all): 5,000 words max
   - CLAUDE.md: 800 words max
5. **Connection density**: For each module, check it has >=2 connections in its ## Connections section

## Output Format

```
VAULT HEALTH REPORT — {date}
================================
Orphans: {count} files ({list})
Broken links: {count} ({list})
Stale files: {count} (>30 days: {list})
Token budgets: {category}: {current}/{max} ({percentage}%)
Connection gaps: {count} modules with <2 connections
================================
Overall: HEALTHY | NEEDS ATTENTION | OVERHAUL RECOMMENDED
```
