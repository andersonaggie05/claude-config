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
- Run lint and tests on changed files before marking work complete
- Write tests for new logic; don't skip tests to save time
- Python: prefer pytest; JS/TS: prefer vitest

## Linting & Formatting
- Always auto-format files you edited (not entire directories)
- Python: prefer ruff (check --fix + format)
- JS/TS: Prettier enforced by pre-commit hook; eslint for linting

## Security
- Never commit .env files, credentials, API keys, or secrets
- Validate inputs at system boundaries (user input, external APIs)

## Planning
- Plan review enforced by plan-review-gate hook (blocks ExitPlanMode without review)
- Never lower test coverage thresholds or quality gates to fix CI — write tests instead

## Workflow
- For all task execution, follow the workflow-protocol skill. It governs assessment, execution, team dispatch, and retrospective.
- Agent knowledge modules are in `~/.claude/modules/`. The director composes these per-task during team dispatch. Do not load module content into the main conversation.

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

Full command reference: `~/.claude/docs/rtk-reference.md` (read only when you need a specific command)
<!-- /rtk-instructions -->