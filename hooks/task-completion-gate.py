#!/usr/bin/env python3
"""
PreToolUse hook for TaskUpdate.
When status == "completed", injects a verification checklist prompt.
Since hooks cannot hard-block, this functions as a mandatory prompt injector.
"""
import json
import sys


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = hook_input.get("tool_input", {})
        if isinstance(tool_input, str):
            tool_input = json.loads(tool_input)
    except Exception:
        sys.exit(0)

    status = tool_input.get("status", "")
    if status != "completed":
        sys.exit(0)

    task_id = tool_input.get("id", tool_input.get("task_id", "unknown"))

    print(
        f"VERIFICATION REQUIRED: Before marking task #{task_id} complete, confirm:\n"
        "- Have ALL checklist items been addressed?\n"
        "- Have tests been run and passed (quote output)?\n"
        "- Has linting passed (ruff/eslint)?\n"
        "- Has Prettier been run on any frontend files?\n"
        "- Do changes match the task description?\n"
        "Re-attempt TaskUpdate after confirming all items.",
        file=sys.stdout,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
