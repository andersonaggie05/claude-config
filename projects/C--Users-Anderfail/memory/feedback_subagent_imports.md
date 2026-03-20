---
name: feedback_subagent_imports
description: When dispatching subagents to write code in Appendix K, include correct import paths (e.g. apps.accounts.models for User, not apps.users.models)
type: feedback
---

When dispatching subagents to create files in Appendix K, include the correct import paths explicitly. The User model is at `apps.accounts.models.User`, not `apps.users.models`. Subagents guess wrong when not told.

**Why:** Phase 4 backend agent used `from apps.users.models import User` — caused ModuleNotFoundError. Had to fix manually after the agent finished.

**How to apply:** In subagent prompts that create Python files, include a "correct imports" section listing the actual model locations. Check existing test files in the same directory for the pattern.
