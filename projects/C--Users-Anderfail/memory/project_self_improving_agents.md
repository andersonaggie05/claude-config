---
name: project_self_improving_agents
description: Self-improving agent ecosystem — workflow-protocol skill, knowledge modules, hard enforcement hooks, automatic retrospective, Obsidian vault integration
type: project
---

Self-improving agent ecosystem. Architecture overhauled 2026-03-16 to replace ad-hoc skills and agent definitions with a unified, mechanically-enforced system.

**Why:** Advisory-only rules were being skipped under context pressure (missing plan reviews, incomplete task gates, skipped Prettier). The fix is mechanical enforcement, not better reminders.

**Core components:**

- **workflow-protocol skill** (`~/.claude/skills/workflow-protocol/`) — single entry point replacing the old workflow-orchestration, agent-pipelines, and retrospective skills. Governs assessment, execution, team dispatch, and retrospective in one place.
- **Knowledge modules** (`~/.claude/modules/`) — composable expertise files (verification, architecture, compliance-audit, security-review, prioritization, completion-checklist). The director loads these per-task during team dispatch; they are never loaded into the main conversation.
- **Hard enforcement hooks** — four hooks that block execution if process steps are skipped:
  - `pre-commit`: blocks commits that skip Prettier or tests
  - `plan-review-gate`: blocks ExitPlanMode if the plan review loop was not run
  - `task-completion-gate`: blocks task completion if the completion checklist was not run
  - `retrospective-gate`: blocks session end if retrospective was not run
- **Automatic 3-layer retrospective** — learning loop at session end: (1) work review (what was built, what broke), (2) process review (which hooks fired, which steps were skipped), (3) system evolution (skill proposals, module updates, memory updates).
- **Obsidian vault** (`~/vault/`) — long-lived knowledge graph with atomic notes, prose-as-title naming, wikilinks. Folders: inbox, claims, frameworks, projects, maps, sources, templates. Browsable in Obsidian GUI.
- **qmd MCP** — hybrid search (BM25 + vector + reranking) and structured queries over the vault. Registered at user scope. Uses `node .../qmd.js mcp`.
- **Smart Connections MCP** — semantic search using Obsidian plugin embeddings (`.smart-env/`). Tools: semantic_search, find_related, get_context_blocks. Community-maintained (additive, not critical).
- **Session orientation hook** (`~/.claude/hooks/session-orient.py`) — fires every SessionStart (no matcher). Queries hermes-bridge + qmd, injects combined context. Graceful degradation on failure.
- **brain-ingest** (`~/.claude/scripts/brain-ingest.py`) — CLI tool to fetch YouTube transcripts, PDFs, text files into `~/vault/inbox/`. Two-stage: brain-ingest fetches raw, then /vault-ingest extracts knowledge.

**Hermes-bridge** (cross-session search and checkpointing, unchanged):
- MCP server with 6 tools: `session_search`, `session_index`, `checkpoint_save`, `checkpoint_restore`, `deliverable_save`, `deliverable_search`
- SQLite DB: `~/.claude/hermes-bridge/data/bridge.db`
- Hooks: SessionEnd (auto-index), PreCompact (checkpoint), SessionStart[compact] (inject context)

## Connections
- Related: [[workflow-protocol]], [[verification]], [[completion-checklist]]
- Tags: #project #system-architecture
