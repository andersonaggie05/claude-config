"""Spike hook: logs stdin JSON payload to data/spike-log.txt for validation."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = LOG_DIR / "spike-log.txt"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now(timezone.utc).isoformat()}] ERROR reading stdin: {e}\n")
        return

    event = payload.get("hook_event_name", "unknown")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now(timezone.utc).isoformat()}] EVENT: {event}\n")
        f.write(f"KEYS: {sorted(payload.keys())}\n")
        # Log full payload but truncate large values
        for key, value in sorted(payload.items()):
            val_str = json.dumps(value) if not isinstance(value, str) else value
            if len(val_str) > 500:
                val_str = val_str[:500] + "...(truncated)"
            f.write(f"  {key}: {val_str}\n")

    # For SessionStart[compact], test additionalContext injection
    if event == "SessionStart":
        result = {
            "hookSpecificOutput": {
                "additionalContext": ("[SPIKE TEST] SessionStart compact hook fired successfully.")
            }
        }
        json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
