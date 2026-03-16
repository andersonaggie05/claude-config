#!/usr/bin/env python3
"""
PreToolUse hook for ExitPlanMode.
Checks transcript for evidence that a Plan review agent was dispatched.
Injects a blocking message if no evidence is found.
"""
import json
import sys


REVIEW_MARKERS = [
    '"subagent_type": "Plan"',
    '"subagent_type":"Plan"',
    "plan review",
    "Plan review",
    "plan-review",
    "review the plan",
    "reviewing the plan",
]


def has_review_evidence(transcript_path: str) -> bool:
    try:
        with open(transcript_path, encoding="utf-8") as f:
            content = f.read()
        return any(marker in content for marker in REVIEW_MARKERS)
    except Exception:
        return False


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")

    if not transcript_path:
        sys.exit(0)

    if has_review_evidence(transcript_path):
        sys.exit(0)

    print(
        "BLOCKED: Plan review loop has not been executed. "
        "Dispatch a Plan review agent before exiting plan mode. "
        "This is a mandatory gate — see workflow-protocol rule #2.",
        file=sys.stdout,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
