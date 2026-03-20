---
name: vault-review
description: Interactive review of pending system improvements from retrospectives
---

# /vault-review

Review accumulated system improvement proposals and triage vault inbox.

## Process

1. Read system-health-board.md for backlog items
2. Read ~/vault/inbox/ for uncategorized items
3. Read declined-proposals.md for context on what was already rejected
4. Present each pending item for user decision: implement, defer, decline
5. Update boards and files based on decisions

## Vault Inbox Triage

6. Scan ~/vault/inbox/ for notes with `status: inbox` in frontmatter
7. Present each inbox note to user for categorization:
   - Move to ~/vault/claims/ — factual claims, assertions, hypotheses
   - Move to ~/vault/frameworks/ — mental models, processes, methodologies
   - Move to ~/vault/sources/ — reference material, external documents
   - Delete — not worth keeping
8. Update the note's `status` field from `inbox` to the chosen category
9. Add [[wikilinks]] to related vault notes during triage
