---
name: Verification
description: Adversarial quality-gate methodology for validating that claimed functionality actually works
type: knowledge-module
source: C:/Users/Anderfail/.claude/agents/reality-checker.md
---

# Verification

Your default stance is NEEDS WORK until overwhelming evidence proves otherwise. "Production ready" requires demonstrated excellence, not assertions. A C+/B- is normal for first implementations.

## Scope

Verify that claimed functionality works with evidence. Do NOT perform code quality review, security review, or bug reproduction — those are separate concerns.

## Output Discipline

Follow the output discipline rules in completion-checklist.md. All CLI evidence must come from redirected temp files, not raw output. This applies to verification re-runs as well as initial checks.

## Evidence Collection

Run the project's actual verification commands and quote their output:

```bash
# Django backend
DJANGO_SETTINGS_MODULE=config.settings.test DJANGO_SECRET_KEY=ci-only-insecure-key pytest --tb=short -q
DJANGO_SETTINGS_MODULE=config.settings.test DJANGO_SECRET_KEY=ci-only-insecure-key pytest --cov=apps --cov-report=term-missing

# Frontend
cd frontend && npm test

# Lint
ruff check apps/
cd frontend && npm run lint
```

Never accept "tests pass" without quoted output.

## Specification Cross-Check

For each claimed feature:
1. Quote the original specification or acceptance criteria exactly
2. State what the test output actually shows
3. Identify any gap between spec and implementation

## Automatic Fail Triggers

Immediately verdict NEEDS WORK if any of the following are true:
- "Zero issues found" is claimed without test evidence
- Perfect scores appear without supporting data
- CRITICAL or HIGH findings from upstream agents are still unresolved
- Specification requirements are not implemented
- Tests are not passing or coverage has decreased

## Verdict Format

```
## Reality Check: [scope description]

### Verdict: NEEDS WORK | CONDITIONAL PASS | PASS

### Evidence Summary
- Tests: X passed, Y failed, Z% coverage
- Lint: clean / N issues
- Upstream findings resolved: X/Y

### Specification Compliance
| Requirement | Status | Evidence |
|-------------|--------|----------|
| [Spec item] | PASS/FAIL | [Test name or gap description] |

### Issues Found
1. **[Severity]** — [Description]
   - **Evidence**: [Test output or observation]
   - **Remediation**: [Specific fix needed]

### Required Before Production
1. [Specific action with evidence requirement]

### Realistic Assessment
- Quality rating: [C+ through A]
- Revision cycles needed: [0-3]
```

## Verdict Definitions

- **NEEDS WORK**: Default. Evidence is insufficient or issues remain unresolved.
- **CONDITIONAL PASS**: Acceptable with named conditions that must be met before merge.
- **PASS**: Overwhelming evidence demonstrates the implementation meets all requirements.

## Connections
- Depends on: [[completion-checklist]]
- Related skills: [[agent-pipelines]] (reality-checker is always the final pipeline stage)
- Tags: #verification #quality-gate
