# Global Claude Code Preferences

## Git
- Always create new commits (never amend unless asked)
- Commit messages: concise, imperative mood, explain "why" not "what"

## Code Style
- Keep changes minimal — only modify what's requested
- No unnecessary comments, docstrings, or type annotations on untouched code
- Prefer editing existing files over creating new ones
- Type hints encouraged for Python
- Never edit lock files or generated build artifacts directly

## Communication
- Be concise, no emojis unless asked
- When referencing code, use `file_path:line_number` format

Project-level CLAUDE.md overrides all global defaults below.

## Context Management
- Suggest /clear when the user switches to an unrelated task
- Proactively suggest committing at natural milestones before long operations

## Testing
- **Verification order:** `tsc --noEmit` → ESLint/ruff → test suite. Type errors are cheapest to catch; don't burn a full test run to discover them.
- Run lint and tests on changed files before marking work complete
- Write tests for new logic; don't skip tests to save time
- Python: prefer pytest; JS/TS: prefer vitest
- Never modify a test just to force it to pass — if a test reveals a real bug, fix the site, not the test
- Tests that enforce implementation style (e.g., "no innerHTML") are fragile — prefer testing behavior over implementation constraints. When a legitimate pattern change breaks a style test, update the test to accommodate the new pattern rather than avoiding the pattern

## Linting & Formatting
- Always auto-format files you edited (not entire directories)
- Python: prefer ruff (check --fix + format)
- JS/TS: Prettier enforced by pre-commit hook; eslint for linting
- When starting a feature branch, run full lint suite first and commit formatting fixes as the first commit — separates cleanup noise from feature work in the PR diff

## Security
- Never commit .env files, credentials, API keys, or secrets
- Validate inputs at system boundaries (user input, external APIs)

## Planning
- Plan review enforced by plan-review-gate hook (blocks ExitPlanMode without review)
- Never lower test coverage thresholds or quality gates to fix CI — write tests instead
- Plans must read actual model/schema files before writing code snippets — never rely on memory or spec assumptions for field names, required args, or FK relationships
- When dispatching implementer subagents, include actual model class definitions in the prompt context
- Diagnosis steps in plans should frame root causes as hypotheses to investigate, not assertions of fact — "investigate what the number is" not "the number is X"
- When dispatching subagents to modify files, include any tests that assert invariants about those files (e.g., "no innerHTML usage") so agents don't unknowingly violate them
- Every plan must include a **Requirements Traceability** section that maps each stated user problem/request to the specific plan step that solves it. If any user requirement has no corresponding solution in the plan, flag it before starting execution. This is enforced by the plan-review-gate hook.

## Workflow
- **Intent check at phase boundaries:** At the end of each release/phase, re-read the user's original request and verify the completed work actually addresses their stated problems — not just the plan's literal instructions. If a gap is found, flag it immediately rather than continuing to the next phase.

## Knowledge Graph (Obsidian Vault)

Three-layer persistence architecture:
- **hermes-bridge** — session memory (ephemeral, cross-session search/checkpoints)
- **Memory files** — Claude preferences and feedback (medium-lived)
- **Obsidian vault** (`~/vault/`) — long-lived knowledge graph with atomic notes

Vault structure: `inbox/`, `claims/`, `frameworks/`, `projects/`, `maps/`, `sources/`, `templates/`
- Prose-as-title naming for claims/frameworks (e.g., "mechanical enforcement beats advisory rules.md")
- YAML frontmatter + wikilinks on all notes

**MCP servers for vault access:**
- **qmd** — hybrid BM25+vector+reranking search, structured queries by path/tag/glob
- **Smart Connections** — semantic search using Obsidian plugin embeddings (additive, not critical)

**Key tools:**
- `brain-ingest.py` (`~/.claude/scripts/`) — CLI to ingest YouTube/PDF/text into `~/vault/inbox/`
- `/vault-ingest` — extract claims/frameworks from inbox notes into structured vault notes
- `/vault-reindex` — regenerate qmd embeddings after vault changes
- `/vault-health` — check vault staleness, orphans, index freshness

**Auto-extraction:** `session-extract.py` hook fires every SessionEnd, scans transcript for retrospectives, decisions, and corrections, creates draft inbox notes in `~/vault/inbox/`. Triage via `/vault-review`.

**Note lifecycle:** `inbox` → `active` → `superseded`. Conflict detection during `/vault-review` triage prevents contradictory knowledge from accumulating.

**Session orientation:** `session-orient.py` hook fires every SessionStart, queries hermes-bridge + qmd, injects combined context. No Obsidian app required at runtime.

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->