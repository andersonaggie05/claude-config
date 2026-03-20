#!/usr/bin/env python3
"""
PreToolUse hook for ExitPlanMode.
Checks transcript for evidence that a Plan review agent was dispatched.
Checks plan file for a Requirements Traceability section.
Injects a blocking message if either check fails.
"""
import json
import os
import glob
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

TRACEABILITY_MARKERS = [
    "requirements traceability",
    "Requirements Traceability",
    "## Requirements",
    "requirement.*→",
    "requirement.*->",
]


def has_review_evidence(transcript_path: str) -> bool:
    try:
        with open(transcript_path, encoding="utf-8") as f:
            content = f.read()
        return any(marker in content for marker in REVIEW_MARKERS)
    except Exception:
        return False


def find_plan_file(cwd: str) -> str | None:
    """Find the most recently modified plan file in .claude/plans/."""
    plans_dir = os.path.join(cwd, ".claude", "plans")
    if not os.path.isdir(plans_dir):
        return None
    files = glob.glob(os.path.join(plans_dir, "*.md"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def has_traceability_section(plan_path: str) -> bool:
    """Check if plan file contains a Requirements Traceability section."""
    try:
        with open(plan_path, encoding="utf-8") as f:
            content = f.read().lower()
        return any(marker.lower() in content for marker in TRACEABILITY_MARKERS)
    except Exception:
        return False


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())

    if not transcript_path:
        sys.exit(0)

    # Check 1: Plan review agent dispatched
    if not has_review_evidence(transcript_path):
        print(
            "BLOCKED: Plan review loop has not been executed. "
            "Dispatch a Plan review agent before exiting plan mode. "
            "This is a mandatory gate — see workflow-protocol rule #2.",
            file=sys.stdout,
        )
        sys.exit(1)

    # Check 2: Requirements traceability section exists in plan
    plan_file = find_plan_file(cwd)
    if plan_file and not has_traceability_section(plan_file):
        print(
            "BLOCKED: Plan file is missing a Requirements Traceability section. "
            "Add a section mapping each user requirement to the plan step that solves it. "
            "This ensures the plan actually addresses the user's stated problems.",
            file=sys.stdout,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
