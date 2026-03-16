#!/usr/bin/env python3
"""
PostToolUse hook for TaskUpdate.
When status == "completed", checks transcript for retrospective evidence.
Injects a reminder if no retrospective markers are found.
"""
import json
import sys


RETRO_MARKERS = [
    "Layer 1: Work Review",
    "Layer 2: Process Review",
    "Layer 3: System Evolution",
    "## Work Review",
    "## Process Review",
    "## System Evolution",
    "3-layer retrospective",
]

REMINDER = (
    "REMINDER: Task marked complete. When ALL plan tasks are done, run the mandatory "
    "3-layer retrospective (Layer 1: Work Review, Layer 2: Process Review, "
    "Layer 3: System Evolution) before declaring work complete. "
    "This is enforced by workflow-protocol rule #6."
)


def has_retro_evidence(transcript_path: str) -> bool:
    try:
        with open(transcript_path, encoding="utf-8") as f:
            content = f.read()
        return any(marker in content for marker in RETRO_MARKERS)
    except Exception:
        return False


def is_completion_event(hook_input: dict) -> bool:
    try:
        tool_input = hook_input.get("tool_input", {})
        if isinstance(tool_input, str):
            tool_input = json.loads(tool_input)
        return tool_input.get("status", "") == "completed"
    except Exception:
        return False


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if not is_completion_event(hook_input):
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")

    if transcript_path and has_retro_evidence(transcript_path):
        sys.exit(0)

    # No transcript available OR no retro evidence found — inject reminder
    print(REMINDER, file=sys.stdout)
    sys.exit(1)


if __name__ == "__main__":
    main()
